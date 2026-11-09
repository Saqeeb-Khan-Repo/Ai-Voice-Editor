from typing import Optional, Dict, Any
from pydantic import BaseModel

class QualityComparisonMetrics(BaseModel):
    duration_passed: bool
    duration_delta_seconds: float
    clipping_resolved: bool
    original_clipped_samples: int
    processed_clipped_samples: int
    original_integrated_lufs: Optional[float]
    processed_integrated_lufs: Optional[float]
    original_true_peak_dbtp: Optional[float]
    processed_true_peak_dbtp: Optional[float]
    original_rms_dbfs: float
    processed_rms_dbfs: float
    original_crest_factor_db: float
    processed_crest_factor_db: float
    estimated_snr_change_db: Optional[float]
    nan_inf_check_passed: bool
    silence_dropout_detected: bool
    overall_quality_passed: bool
    quality_summary: str

class AudioOutputMetadata(BaseModel):
    id: str
    job_id: str
    audio_file_id: str
    filename: str
    file_format: str
    file_size_bytes: int
    metrics: Dict[str, Any]
    quality_report: QualityComparisonMetrics
    created_at: str
