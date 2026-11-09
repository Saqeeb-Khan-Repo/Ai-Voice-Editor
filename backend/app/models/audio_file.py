import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON
from app.database.session import Base

class AudioFile(Base):
    __tablename__ = "audio_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_filename = Column(String(255), nullable=False)
    sanitized_filename = Column(String(255), nullable=False)
    file_format = Column(String(10), nullable=False)
    duration_seconds = Column(Float, nullable=False, default=0.0)
    sample_rate = Column(Integer, nullable=False, default=44100)
    channels = Column(Integer, nullable=False, default=1)
    file_size_bytes = Column(Integer, nullable=False, default=0)
    storage_relative_path = Column(String(500), nullable=False)
    analysis_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "sanitized_filename": self.sanitized_filename,
            "file_format": self.file_format,
            "duration_seconds": self.duration_seconds,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "file_size_bytes": self.file_size_bytes,
            "analysis": self.analysis_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
