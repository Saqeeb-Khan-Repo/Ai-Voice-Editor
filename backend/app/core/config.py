import os
from pathlib import Path
from typing import List, Literal
from pydantic_settings import BaseSettings

IS_VERCEL = os.environ.get("VERCEL") == "1" or os.environ.get("VERCEL_ENV") is not None

class Settings(BaseSettings):
    APP_NAME: str = "AI Naat Studio"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    IS_VERCEL: bool = IS_VERCEL
    
    # Server Binding
    HOST: str = "0.0.0.0" if IS_VERCEL else "127.0.0.1"
    PORT: int = int(os.environ.get("PORT", 8000))
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ]
    
    # Storage Paths: on Vercel lambda /tmp is the only writable filesystem
    BASE_DIR: Path = Path("/tmp") if IS_VERCEL else Path(__file__).resolve().parent.parent.parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    ORIGINALS_DIR: Path = STORAGE_DIR / "originals"
    PROCESSED_DIR: Path = STORAGE_DIR / "processed"
    TEMPORARY_DIR: Path = STORAGE_DIR / "temporary"
    DATABASE_PATH: Path = STORAGE_DIR / "ai_naat_studio.db"

    # Bundled sample audio path (inside backend or repo root)
    SAMPLES_DIR: Path = Path(__file__).resolve().parent.parent.parent / "samples"
    
    # Upload limits
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_EXTENSIONS: List[str] = [".wav", ".mp3", ".flac", ".webm", ".ogg", ".m4a"]
    
    # Audio Engine defaults
    TARGET_LUFS: float = -16.0
    TRUE_PEAK_CEILING_DBTP: float = -1.0
    DEFAULT_SAMPLE_RATE: int = 44100
    
    # Model configuration
    ACTIVE_NOISE_REDUCER: Literal["auto", "spectral_gating", "deepfilternet", "passthrough"] = "auto"
    FORCE_CPU: bool = True
    
    # Cleanup retention
    TEMP_FILE_RETENTION_HOURS: int = 24

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure storage directories exist safely
try:
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    settings.ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
    settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    settings.TEMPORARY_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass
