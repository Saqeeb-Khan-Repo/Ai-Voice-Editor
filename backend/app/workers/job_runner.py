import os
import time
import logging
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional

from app.core.config import settings
from app.database.session import SessionLocal
from app.models.processing_job import ProcessingJob
from app.models.audio_file import AudioFile
from app.models.audio_output import AudioOutput
from app.audio_engine.pipeline import AudioEnhancementPipeline

logger = logging.getLogger(__name__)

class BackgroundJobRunner:
    """
    Non-blocking background job processor.
    Runs CPU-intensive audio DSP on dedicated worker threads,
    reports real-time progress to SQLite, and supports cancellation.
    """
    def __init__(self, max_workers: int = 2):
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="naat_dsp_worker")
        self._cancellation_tokens: Dict[str, bool] = {}
        self.pipeline = AudioEnhancementPipeline(preferred_nr_backend=settings.ACTIVE_NOISE_REDUCER)

    def request_cancellation(self, job_id: str) -> bool:
        if job_id in self._cancellation_tokens:
            self._cancellation_tokens[job_id] = True
            return True
        return False

    def recover_interrupted_jobs(self):
        """Called on app startup to cleanly transition any stale jobs."""
        with SessionLocal() as session:
            stale_jobs = session.query(ProcessingJob).filter(
                ProcessingJob.status.in_(["pending", "analyzing", "denoising", "filtering", "equalizing",
                                         "compressing", "deessing", "reverberating", "normalizing",
                                         "limiting", "validating", "exporting"])
            ).all()
            for job in stale_jobs:
                job.status = "failed"
                job.error_message = "Server restarted while processing was active. Job terminated cleanly."
                job.completed_at = datetime.utcnow()
            session.commit()
            if stale_jobs:
                logger.info(f"Recovered {len(stale_jobs)} interrupted jobs on startup.")

    def submit_job(self, job_id: str):
        """Enqueues job to run asynchronously in worker thread pool."""
        self._cancellation_tokens[job_id] = False
        self.executor.submit(self._run_job_lifecycle, job_id)

    def _update_job_status(
        self,
        job_id: str,
        status: str,
        stage: str,
        progress: int,
        error_msg: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        decision_log: Optional[Dict[str, Any]] = None
    ):
        try:
            with SessionLocal() as session:
                job = session.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
                if job:
                    job.status = status
                    job.current_stage = stage
                    job.progress_percent = progress
                    if error_msg:
                        job.error_message = error_msg
                    if execution_time_ms:
                        job.execution_time_ms = execution_time_ms
                    if decision_log:
                        job.decision_log = decision_log
                    if status in ["completed", "failed", "cancelled"]:
                        job.completed_at = datetime.utcnow()
                    session.commit()
        except Exception as e:
            logger.error(f"Failed to update job progress in DB: {e}")

    def _run_job_lifecycle(self, job_id: str):
        start_time = time.time()

        with SessionLocal() as session:
            job = session.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found in database.")
                return

            audio_file = session.query(AudioFile).filter(AudioFile.id == job.audio_file_id).first()
            if not audio_file:
                job.status = "failed"
                job.error_message = "Associated audio file not found."
                session.commit()
                return

            input_rel_path = audio_file.storage_relative_path
            config = job.config_parameters or {}
            analysis_data = audio_file.analysis_data
            job.status = "analyzing"
            job.started_at = datetime.utcnow()
            session.commit()

        input_abs_path = os.path.join(settings.BASE_DIR, input_rel_path)
        out_fmt = config.get("output_format", "wav").lower()
        output_filename = f"enhanced_{job_id[:8]}.{out_fmt}"
        output_rel_path = os.path.join("storage", "processed", f"{job_id}_{output_filename}").replace("\\", "/")
        output_abs_path = os.path.join(settings.BASE_DIR, output_rel_path)

        def sync_progress_callback(stage: str, percent: int):
            self._update_job_status(job_id, stage, stage, percent)

        def check_cancelled() -> bool:
            return self._cancellation_tokens.get(job_id, False)

        try:
            result = self.pipeline.process_file(
                input_abs_path,
                output_abs_path,
                config,
                analysis_data,
                sync_progress_callback,
                check_cancelled
            )

            elapsed_ms = int((time.time() - start_time) * 1000)
            file_size = os.path.getsize(output_abs_path) if os.path.exists(output_abs_path) else 0

            with SessionLocal() as session:
                audio_output = AudioOutput(
                    job_id=job_id,
                    audio_file_id=audio_file.id,
                    filename=output_filename,
                    file_format=out_fmt,
                    file_size_bytes=file_size,
                    storage_relative_path=output_rel_path,
                    metrics=result["processed_analysis"],
                    quality_report=result["comparison_report"]
                )
                session.add(audio_output)

                job = session.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
                if job:
                    job.status = "completed"
                    job.current_stage = "completed"
                    job.progress_percent = 100
                    job.execution_time_ms = elapsed_ms
                    job.completed_at = datetime.utcnow()
                session.commit()

            logger.info(f"Job {job_id} successfully completed in {elapsed_ms}ms.")

        except InterruptedError:
            logger.info(f"Job {job_id} was successfully cancelled.")
            if os.path.exists(output_abs_path):
                try:
                    os.remove(output_abs_path)
                except OSError:
                    pass
            self._update_job_status(
                job_id, "cancelled", "cancelled", 0, error_msg="Cancelled by user"
            )
        except Exception as e:
            err_details = str(e)
            logger.error(f"Error processing job {job_id}: {err_details}\n{traceback.format_exc()}")
            self._update_job_status(
                job_id, "failed", "failed", 0, error_msg=err_details
            )
        finally:
            self._cancellation_tokens.pop(job_id, None)

job_runner = BackgroundJobRunner()
