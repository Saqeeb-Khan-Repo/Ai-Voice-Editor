import os
import shutil
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.models.audio_file import AudioFile
from app.models.processing_job import ProcessingJob
from app.models.audio_output import AudioOutput

router = APIRouter(prefix="/settings", tags=["Settings"])

class SettingsUpdateSchema(BaseModel):
    max_upload_size_mb: Optional[int] = Field(None, ge=5, le=500)
    default_output_format: Optional[str] = Field(None, pattern="^(wav|mp3|flac)$")
    active_noise_reducer: Optional[str] = Field(None, pattern="^(auto|spectral_gating|deepfilternet|passthrough)$")
    force_cpu: Optional[bool] = None

@router.get("")
def get_current_settings():
    return {
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
        "allowed_extensions": settings.ALLOWED_EXTENSIONS,
        "default_target_lufs": settings.TARGET_LUFS,
        "default_true_peak_ceiling_dbtp": settings.TRUE_PEAK_CEILING_DBTP,
        "default_sample_rate": settings.DEFAULT_SAMPLE_RATE,
        "active_noise_reducer": settings.ACTIVE_NOISE_REDUCER,
        "force_cpu": settings.FORCE_CPU,
        "temp_retention_hours": settings.TEMP_FILE_RETENTION_HOURS,
    }

@router.post("")
def update_settings(payload: SettingsUpdateSchema):
    if payload.max_upload_size_mb is not None:
        settings.MAX_UPLOAD_SIZE_MB = payload.max_upload_size_mb
    if payload.active_noise_reducer is not None:
        settings.ACTIVE_NOISE_REDUCER = payload.active_noise_reducer
    if payload.force_cpu is not None:
        settings.FORCE_CPU = payload.force_cpu
    return {
        "message": "Settings updated successfully",
        "settings": get_current_settings()
    }

@router.post("/clear-all-data")
def clear_all_studio_data(db: Session = Depends(get_db)):
    """
    Complete reset of all session data:
    Removes all original audio, processed files, temporary caches, and database rows.
    """
    db.query(AudioOutput).delete()
    db.query(ProcessingJob).delete()
    db.query(AudioFile).delete()
    db.commit()

    for folder in [settings.ORIGINALS_DIR, settings.PROCESSED_DIR, settings.TEMPORARY_DIR]:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception:
                    pass

    return {"message": "All session audio, job history, and storage data have been safely wiped."}
