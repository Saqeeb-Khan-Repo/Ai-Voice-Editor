import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey
from app.database.session import Base

class AudioOutput(Base):
    __tablename__ = "audio_outputs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False)
    audio_file_id = Column(String(36), ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_format = Column(String(10), nullable=False)
    file_size_bytes = Column(Integer, nullable=False, default=0)
    storage_relative_path = Column(String(500), nullable=False)
    metrics = Column(JSON, nullable=True)
    quality_report = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "audio_file_id": self.audio_file_id,
            "filename": self.filename,
            "file_format": self.file_format,
            "file_size_bytes": self.file_size_bytes,
            "metrics": self.metrics,
            "quality_report": self.quality_report,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
