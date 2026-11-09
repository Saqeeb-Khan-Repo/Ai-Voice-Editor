import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.session import get_db
from app.models.audio_file import AudioFile
from app.models.processing_job import ProcessingJob
from app.models.audio_output import AudioOutput
from app.schemas.processing import ProcessingRequest, ProcessingJobResponse, JobListResponse
from app.audio_engine.decision_engine import EnhancementDecisionEngine
from app.workers.job_runner import job_runner

router = APIRouter(tags=["Processing"])

@router.post("/processing/{audio_id}", response_model=ProcessingJobResponse, status_code=status.HTTP_202_ACCEPTED)
def start_processing_job(
    audio_id: str,
    req: ProcessingRequest,
    db: Session = Depends(get_db)
):
    audio = db.query(AudioFile).filter(AudioFile.id == audio_id).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Audio file not found")

    if not audio.analysis_data:
        raise HTTPException(status_code=400, detail="Audio analysis must be completed before processing")

    config, decision_log = EnhancementDecisionEngine.decide(
        analysis=audio.analysis_data,
        preset=req.preset,
        automatic_mode=req.automatic_mode,
        overrides=req.overrides
    )

    job_id = str(uuid.uuid4())
    job = ProcessingJob(
        id=job_id,
        audio_file_id=audio.id,
        status="pending",
        current_stage="queued",
        progress_percent=0,
        preset_name=req.preset,
        config_parameters=config,
        decision_log=decision_log,
        created_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Submit to non-blocking worker thread pool
    job_runner.submit_job(job_id)

    return ProcessingJobResponse(
        job_id=job.id,
        audio_id=job.audio_file_id,
        status=job.status,
        current_stage=job.current_stage,
        progress_percent=job.progress_percent,
        preset_name=job.preset_name,
        config_parameters=job.config_parameters,
        decision_log=decision_log,
        created_at=job.created_at.isoformat()
    )

@router.get("/jobs/{job_id}", response_model=ProcessingJobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")

    output_id = None
    if job.status == "completed":
        out = db.query(AudioOutput.id).filter(AudioOutput.job_id == job.id).first()
        if out:
            output_id = out[0]

    return ProcessingJobResponse(
        job_id=job.id,
        audio_id=job.audio_file_id,
        status=job.status,
        current_stage=job.current_stage,
        progress_percent=job.progress_percent,
        preset_name=job.preset_name,
        config_parameters=job.config_parameters,
        decision_log=job.decision_log,
        output_id=output_id,
        error_message=job.error_message,
        execution_time_ms=job.execution_time_ms,
        created_at=job.created_at.isoformat() if job.created_at else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )

@router.get("/jobs", response_model=JobListResponse)
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(ProcessingJob).order_by(desc(ProcessingJob.created_at)).limit(50).all()

    job_responses = []
    for j in jobs:
        out_id = None
        if j.status == "completed":
            out = db.query(AudioOutput.id).filter(AudioOutput.job_id == j.id).first()
            if out:
                out_id = out[0]

        job_responses.append(
            ProcessingJobResponse(
                job_id=j.id,
                audio_id=j.audio_file_id,
                status=j.status,
                current_stage=j.current_stage,
                progress_percent=j.progress_percent,
                preset_name=j.preset_name,
                config_parameters=j.config_parameters,
                decision_log=j.decision_log,
                output_id=out_id,
                error_message=j.error_message,
                execution_time_ms=j.execution_time_ms,
                created_at=j.created_at.isoformat() if j.created_at else None,
                started_at=j.started_at.isoformat() if j.started_at else None,
                completed_at=j.completed_at.isoformat() if j.completed_at else None,
            )
        )

    return JobListResponse(total=len(job_responses), jobs=job_responses)

@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in ["completed", "failed", "cancelled"]:
        return {"message": f"Job is already {job.status}", "job_id": job_id}

    cancelled = job_runner.request_cancellation(job_id)
    job.status = "cancelled"
    job.current_stage = "cancelled"
    job.error_message = "Cancelled by user"
    job.completed_at = datetime.utcnow()
    db.commit()

    return {"message": "Cancellation requested", "job_id": job_id, "success": cancelled}
