from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class ProcessingParametersOverride(BaseModel):
    noise_reduction_enabled: Optional[bool] = None
    noise_reduction_strength: Optional[float] = Field(None, ge=0.0, le=1.0)
    noise_reduction_mode: Optional[str] = Field(None, pattern="^(off|subtle|balanced|aggressive|maximum)$")
    eq_intensity: Optional[float] = Field(None, ge=0.0, le=2.0)
    compression_intensity: Optional[float] = Field(None, ge=0.0, le=1.0)
    reverb_amount: Optional[float] = Field(None, ge=0.0, le=1.0)
    autotune_enabled: Optional[bool] = None
    autotune_strength: Optional[float] = Field(None, ge=0.0, le=1.0)
    autotune_scale: Optional[str] = Field(None, pattern="^(chromatic|hijaz|bayati|minor|major)$")
    echo_enabled: Optional[bool] = None
    echo_amount: Optional[float] = Field(None, ge=0.0, le=1.0)
    echo_delay_ms: Optional[float] = Field(None, ge=100.0, le=600.0)
    echo_feedback: Optional[float] = Field(None, ge=0.05, le=0.6)
    tube_saturation_enabled: Optional[bool] = None
    tube_warmth: Optional[float] = Field(None, ge=0.0, le=1.0)
    doubler_enabled: Optional[bool] = None
    doubler_mix: Optional[float] = Field(None, ge=0.0, le=1.0)
    doubler_width: Optional[float] = Field(None, ge=0.0, le=1.0)
    trim_start_seconds: Optional[float] = Field(None, ge=0.0)
    trim_end_seconds: Optional[float] = Field(None, ge=0.0)
    strip_silence: Optional[bool] = None
    target_lufs: Optional[float] = Field(None, ge=-30.0, le=-6.0)
    true_peak_ceiling: Optional[float] = Field(None, ge=-6.0, le=-0.1)
    output_format: Optional[str] = Field("wav", pattern="^(wav|mp3|flac)$")
    # Clean Studio Controls
    noise_reduction_level: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    reverb_level: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    vocal_warmth: Optional[float] = Field(None, ge=0.0, le=1.0)
    vocal_clarity: Optional[float] = Field(None, ge=0.0, le=1.0)
    compression_amount: Optional[float] = Field(None, ge=0.0, le=1.0)

class ProcessingRequest(BaseModel):
    preset: str = Field(
        "studio_naat",
        pattern="^(natural_naat|studio_naat|spacious_naat|maqam_classical|jalsa_live|modern_nasheed|youth_vocal|deep_baritone|custom)$"
    )
    automatic_mode: bool = True
    custom_profile_id: Optional[str] = None
    overrides: Optional[ProcessingParametersOverride] = None

class ProcessingDecisionLog(BaseModel):
    preset_selected: str
    noise_reduction_decision: str
    high_pass_decision: str
    eq_decision: str
    autotune_decision: Optional[str] = None
    saturation_decision: Optional[str] = None
    compression_decision: str
    deess_decision: str
    doubler_decision: Optional[str] = None
    reverb_decision: str
    echo_decision: Optional[str] = None
    trim_decision: Optional[str] = None
    loudness_decision: str
    limiting_decision: str
    notes: List[str] = []

class ProcessingJobResponse(BaseModel):
    job_id: str
    audio_id: str
    status: str
    current_stage: str
    progress_percent: int
    preset_name: str
    config_parameters: Optional[Dict[str, Any]] = None
    decision_log: Optional[ProcessingDecisionLog] = None
    output_id: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class JobListResponse(BaseModel):
    total: int
    jobs: List[ProcessingJobResponse]
