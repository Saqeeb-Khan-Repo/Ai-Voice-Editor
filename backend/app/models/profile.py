import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from app.database.session import Base

class ReciterProfile(Base):
    __tablename__ = "reciter_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    is_builtin = Column(Boolean, default=False, nullable=False)
    vocal_type = Column(String(50), default="custom", nullable=False)
    settings = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_builtin": self.is_builtin,
            "vocal_type": self.vocal_type,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
