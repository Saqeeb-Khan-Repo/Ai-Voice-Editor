import os
import time
import shutil
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional
import psutil
from sqlalchemy import func

from app.core.config import settings
from app.database.session import SessionLocal
from app.models.processing_job import ProcessingJob
from app.models.audio_file import AudioFile
from app.audio_engine.stages.noise_reduction import DeepFilterNetAdapter

APP_START_TIME = time.time()
_RECENT_ERRORS: List[Dict[str, Any]] = []

def log_system_error(stage: str, message: str, context: Optional[Dict[str, Any]] = None):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "stage": stage,
        "message": message,
        "context": context or {}
    }
    _RECENT_ERRORS.append(entry)
    if len(_RECENT_ERRORS) > 20:
        _RECENT_ERRORS.pop(0)

class MonitoringService:
    @staticmethod
    def get_system_resources() -> Dict[str, Any]:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        return {
            "cpu_percent": round(cpu, 1),
            "memory_used_mb": round(mem.used / (1024 * 1024), 1),
            "memory_total_mb": round(mem.total / (1024 * 1024), 1),
            "memory_percent": round(mem.percent, 1),
        }

    @staticmethod
    def get_storage_usage() -> Dict[str, Any]:
        def dir_size(path):
            total = 0
            if os.path.exists(path):
                for dirpath, _, filenames in os.walk(path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if os.path.exists(fp):
                            total += os.path.getsize(fp)
            return total

        orig_b = dir_size(settings.ORIGINALS_DIR)
        proc_b = dir_size(settings.PROCESSED_DIR)
        temp_b = dir_size(settings.TEMPORARY_DIR)
        db_b = os.path.getsize(settings.DATABASE_PATH) if os.path.exists(settings.DATABASE_PATH) else 0

        total_app = orig_b + proc_b + temp_b + db_b
        disk = shutil.disk_usage(settings.STORAGE_DIR)

        return {
            "originals_bytes": orig_b,
            "processed_bytes": proc_b,
            "temporary_bytes": temp_b,
            "database_bytes": db_b,
            "total_app_storage_bytes": total_app,
            "disk_free_bytes": disk.free,
            "disk_total_bytes": disk.total,
        }

    @staticmethod
    def get_engine_status() -> Dict[str, Any]:
        df_adapter = DeepFilterNetAdapter()
        df_ok, df_reason = df_adapter.is_available()

        ffmpeg_ok = False
        ffmpeg_version = None
        try:
            res = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                ffmpeg_ok = True
                first_line = res.stdout.split("\n")[0]
                ffmpeg_version = first_line.split(" ")[2] if len(first_line.split(" ")) > 2 else "installed"
        except Exception:
            ffmpeg_ok = False

        return {
            "engine_name": "AI Naat Studio Professional Audio Engine",
            "active_noise_reducer": settings.ACTIVE_NOISE_REDUCER,
            "deepfilternet_available": df_ok,
            "deepfilternet_details": df_reason,
            "spectral_gating_available": True,
            "ffmpeg_available": ffmpeg_ok,
            "ffmpeg_version": ffmpeg_version,
            "sample_rate_support": [22050, 44100, 48000, 88200, 96000],
            "device_mode": "CPU (Guaranteed Baseline)",
        }

    @classmethod
    def get_overview(cls) -> Dict[str, Any]:
        uptime = time.time() - APP_START_TIME
        with SessionLocal() as session:
            active_cnt = session.query(func.count(ProcessingJob.id)).filter(
                ProcessingJob.status.in_(["pending", "analyzing", "denoising", "filtering", "equalizing",
                                         "compressing", "deessing", "reverberating", "normalizing",
                                         "limiting", "validating", "exporting"])
            ).scalar() or 0
            completed_cnt = session.query(func.count(ProcessingJob.id)).filter(ProcessingJob.status == "completed").scalar() or 0
            failed_cnt = session.query(func.count(ProcessingJob.id)).filter(ProcessingJob.status == "failed").scalar() or 0
            files_cnt = session.query(func.count(AudioFile.id)).scalar() or 0
            avg_dur = session.query(func.avg(ProcessingJob.execution_time_ms)).filter(ProcessingJob.status == "completed").scalar() or 0.0

        return {
            "backend_status": "healthy",
            "app_version": settings.APP_VERSION,
            "uptime_seconds": round(uptime, 1),
            "active_jobs_count": active_cnt,
            "completed_jobs_count": completed_cnt,
            "failed_jobs_count": failed_cnt,
            "total_audio_files": files_cnt,
            "average_processing_duration_ms": round(float(avg_dur), 1),
            "system_resources": cls.get_system_resources(),
            "engine_status": cls.get_engine_status(),
            "storage_usage": cls.get_storage_usage(),
            "recent_errors": list(_RECENT_ERRORS),
        }
