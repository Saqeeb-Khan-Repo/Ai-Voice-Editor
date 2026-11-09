from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class SystemResources(BaseModel):
    cpu_percent: float
    memory_used_mb: float
    memory_total_mb: float
    memory_percent: float

class StorageUsage(BaseModel):
    originals_bytes: int
    processed_bytes: int
    temporary_bytes: int
    database_bytes: int
    total_app_storage_bytes: int
    disk_free_bytes: int
    disk_total_bytes: int

class AudioEngineStatus(BaseModel):
    engine_name: str
    active_noise_reducer: str
    deepfilternet_available: bool
    deepfilternet_details: str
    spectral_gating_available: bool
    ffmpeg_available: bool
    ffmpeg_version: Optional[str]
    sample_rate_support: List[int]
    device_mode: str

class MonitoringOverview(BaseModel):
    backend_status: str
    app_version: str
    uptime_seconds: float
    active_jobs_count: int
    completed_jobs_count: int
    failed_jobs_count: int
    total_audio_files: int
    average_processing_duration_ms: float
    system_resources: SystemResources
    engine_status: AudioEngineStatus
    storage_usage: StorageUsage
    recent_errors: List[Dict[str, Any]]
