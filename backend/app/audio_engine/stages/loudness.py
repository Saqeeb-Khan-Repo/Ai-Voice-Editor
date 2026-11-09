import math
import numpy as np
import pyloudnorm as pyln
from typing import Dict, Any, Tuple
from app.audio_engine.stages.base import PipelineStage

class LoudnessNormalizationStage(PipelineStage):
    """
    Stage 9: EBU R128 / ITU-R BS.1770 Loudness Normalization.
    Normalizes audio to a standardized target integrated loudness (e.g. -16 LUFS)
    using transparent linear gain adjustment.
    """
    def __init__(self):
        super().__init__("loudness_normalization")

    def process(
        self, audio: np.ndarray, sample_rate: int, config: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        self.validate_audio(audio)
        loud_cfg = config.get("loudness", {})
        target_lufs = float(loud_cfg.get("target_lufs", -16.0))

        # Measure current loudness
        duration = len(audio) / sample_rate
        if duration >= 0.4:
            try:
                meter = pyln.Meter(sample_rate)
                measured_lufs = float(meter.integrated_loudness(audio))
            except Exception:
                rms = float(np.sqrt(np.mean(np.square(audio))))
                measured_lufs = 20.0 * math.log10(max(rms, 1e-9)) - 3.0
        else:
            rms = float(np.sqrt(np.mean(np.square(audio))))
            measured_lufs = 20.0 * math.log10(max(rms, 1e-9)) - 3.0

        if math.isnan(measured_lufs) or math.isinf(measured_lufs) or measured_lufs < -65.0:
            return audio.copy(), {
                "stage": self.name,
                "status": "bypassed",
                "reason": "Signal too low or invalid to measure loudness"
            }

        delta_db = target_lufs - measured_lufs
        # Allow up to +24 dB boost to handle quiet studio mic recordings
        clamped_delta_db = max(-24.0, min(24.0, delta_db))
        gain_linear = 10.0 ** (clamped_delta_db / 20.0)

        normalized = audio * gain_linear

        return normalized.astype(np.float32), {
            "stage": self.name,
            "status": "applied",
            "initial_lufs": round(measured_lufs, 2),
            "target_lufs": round(target_lufs, 2),
            "gain_applied_db": round(clamped_delta_db, 2)
        }
