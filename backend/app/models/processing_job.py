import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey
from app.database.session import Base

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    audio_file_id = Column(String(36), ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(30), nullable=False, default="pending")
    # pending, analyzing, denoising, filtering, equalizing, compressing, deessing, reverberating, normalizing, limiting, validating, exporting, completed, failed, cancelled
    current_stage = Column(String(50), nullable=False, default="queued")
    progress_percent = Column(Integer, nullable=False, default=0)
    preset_name = Column(String(50), nullable=False, default="natural_naat")
    config_parameters = Column(JSON, nullable=True)
    decision_log = Column(JSON, nullable=True)
    error_message = Column(String(1000), nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "audio_file_id": self.audio_file_id,
            "status": self.status,
            "current_stage": self.current_stage,
            "progress_percent": self.progress_percent,
            "preset_name": self.preset_name,
            "config_parameters": self.config_parameters,
            "decision_log": self.decision_log,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
