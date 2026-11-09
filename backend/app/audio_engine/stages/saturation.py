import numpy as np
import scipy.signal
from typing import Dict, Any, Tuple
from app.audio_engine.stages.base import PipelineStage

class WarmTubeSaturationStage(PipelineStage):
    """
    Warm Analog Tube & Tape Saturation Stage.
    Models triode/pentode analog harmonic saturation for studio Naat vocals:
    - Adds subtle 2nd and 3rd harmonics to give warmth and vocal body.
    - Soft-clips harsh transient peaks without digital clipping.
    - High-frequency tape smoothing to round off sibilant harshness.
    """
    def __init__(self):
        super().__init__("tube_saturation")

    def process(
        self, audio: np.ndarray, sample_rate: int, config: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        self.validate_audio(audio)
        sat_cfg = config.get("saturation", {})
        enabled = sat_cfg.get("enabled", False)
        warmth = float(sat_cfg.get("warmth", 0.0))
        drive = float(sat_cfg.get("drive", 1.2))

        if not enabled or warmth <= 0.02:
            return audio.copy(), {
                "stage": self.name,
                "status": "bypassed",
                "warmth": 0.0
            }

        x = audio.copy()
        drive_clamped = max(1.0, min(2.5, drive * (1.0 + warmth * 0.8)))
        asym = x + 0.12 * (x ** 2)
        saturated = np.tanh(drive_clamped * asym) / np.tanh(drive_clamped)

        nyquist = sample_rate * 0.5
        cutoff = min(14000.0, nyquist * 0.9)
        b_tape, a_tape = scipy.signal.butter(1, cutoff / nyquist, btype="low")

        if audio.ndim == 1:
            sat_smooth = scipy.signal.lfilter(b_tape, a_tape, saturated)
        else:
            sat_smooth = np.zeros_like(saturated)
            for ch in range(audio.shape[1]):
                sat_smooth[:, ch] = scipy.signal.lfilter(b_tape, a_tape, saturated[:, ch])

        mix = min(1.0, max(0.0, warmth * 0.45))
        output = (1.0 - mix) * audio + mix * sat_smooth

        return output.astype(np.float32), {
            "stage": self.name,
            "status": "applied",
            "warmth": warmth,
            "drive": round(drive_clamped, 2),
            "mix": round(mix, 3)
        }
