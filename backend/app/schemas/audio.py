from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class FrequencyBandAnalysis(BaseModel):
    sub_bass_energy_db: float = Field(..., description="Energy < 60 Hz")
    bass_energy_db: float = Field(..., description="Energy 60 - 250 Hz")
    low_mid_energy_db: float = Field(..., description="Energy 250 - 500 Hz (warmth/muddiness)")
    mid_energy_db: float = Field(..., description="Energy 500 - 2000 Hz (body/nasal)")
    high_mid_energy_db: float = Field(..., description="Energy 2000 - 5000 Hz (intelligibility/presence)")
    presence_high_energy_db: float = Field(..., description="Energy 5000 - 10000 Hz (sibilance)")
    air_energy_db: float = Field(..., description="Energy > 10000 Hz (air/sparkle)")
    spectral_centroid_hz: float = Field(..., description="Center of spectral mass")
    spectral_rolloff_hz: float = Field(..., description="85% spectral energy frequency")

class AudioQualityProblems(BaseModel):
    has_clipping: bool
    clipped_sample_count: int
    clipped_sample_percentage: float
    has_sub_rumble: bool
    has_boxiness_mud: bool
    has_excessive_sibilance: bool
    has_high_noise_floor: bool
    is_too_quiet: bool
    has_excessive_dynamic_range: bool
    is_mono: bool

class AudioAnalysisReport(BaseModel):
    duration_seconds: float
    sample_rate: int
    channels: int
    peak_amplitude_dbfs: float
    rms_dbfs: float
    crest_factor_db: float
    integrated_lufs: Optional[float] = None
    true_peak_dbtp: Optional[float] = None
    silence_regions: List[Dict[str, float]] = []
    silence_percentage: float = 0.0
    estimated_snr_db: Optional[float] = None
    noise_estimation_confidence: str = Field(
        ..., 
        description="'measured' if verified pause found, 'estimated' if derived from lowest energy frames"
    )
    frequency_bands: FrequencyBandAnalysis
    quality_problems: AudioQualityProblems
    vocal_profile: Optional[Dict[str, Any]] = None
    recommendations: List[str]

class AudioFileMetadata(BaseModel):
    id: str
    original_filename: str
    sanitized_filename: str
    file_format: str
    duration_seconds: float
    sample_rate: int
    channels: int
    file_size_bytes: int
    created_at: str
    analysis: Optional[AudioAnalysisReport] = None

class AudioUploadResponse(BaseModel):
    audio_id: str
    filename: str
    duration_seconds: float
    sample_rate: int
    channels: int
    file_size_bytes: int
    analysis: AudioAnalysisReport
    message: str = "Audio uploaded and analyzed successfully"

class AudioEditRequest(BaseModel):
    start_seconds: Optional[float] = Field(0.0, ge=0.0)
    end_seconds: Optional[float] = Field(None, ge=0.0)
    strip_silence: Optional[bool] = False
    gain_db: Optional[float] = Field(0.0, ge=-24.0, le=24.0)
