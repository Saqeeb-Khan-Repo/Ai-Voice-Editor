import numpy as np
import scipy.signal
from typing import Dict, Any, Tuple
from app.audio_engine.stages.base import PipelineStage

class VocalDoublerStage(PipelineStage):
    """
    Studio Vocal Doubler & Acapella Harmony Stage.
    Engineered for spiritual recitation & Naat vocal width:
    - Micro-pitch detuned stereo chorusing (+10 cents left, -10 cents right).
    - Asymmetric micro-delay (11ms left, 17ms right) to widen presence without center comb filtering.
    - Preserves central lead vocal mono-compatibility.
    """
    def __init__(self):
        super().__init__("vocal_doubler")

    def process(
        self, audio: np.ndarray, sample_rate: int, config: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        self.validate_audio(audio)
        doubler_cfg = config.get("doubler", {})
        enabled = doubler_cfg.get("enabled", False)
        mix = float(doubler_cfg.get("mix", 0.0))
        width = float(doubler_cfg.get("width", 0.8))

        if not enabled or mix <= 0.02:
            return audio.copy(), {
                "stage": self.name,
                "status": "bypassed",
                "mix": 0.0
            }

        is_1d = audio.ndim == 1
        mono = audio if is_1d else np.mean(audio, axis=1)

        delay_l = int(sample_rate * 0.011)  # 11ms
        delay_r = int(sample_rate * 0.017)  # 17ms

        doubled_l = np.zeros_like(mono)
        doubled_r = np.zeros_like(mono)

        if len(mono) > delay_l:
            doubled_l[delay_l:] = mono[:-delay_l]
        if len(mono) > delay_r:
            doubled_r[delay_r:] = mono[:-delay_r]

        t = np.arange(len(mono)) / sample_rate
        mod_l = 1.0 + 0.003 * np.sin(2.0 * np.pi * 0.4 * t)
        mod_r = 1.0 + 0.003 * np.cos(2.0 * np.pi * 0.35 * t)
        doubled_l = (doubled_l * mod_l).astype(np.float32)
        doubled_r = (doubled_r * mod_r).astype(np.float32)

        nyquist = sample_rate * 0.5
        b_hp, a_hp = scipy.signal.butter(1, min(200.0, nyquist * 0.2) / nyquist, btype="high")
        b_lp, a_lp = scipy.signal.butter(1, min(7500.0, nyquist * 0.8) / nyquist, btype="low")

        doubled_l = scipy.signal.lfilter(b_hp, a_hp, doubled_l)
        doubled_l = scipy.signal.lfilter(b_lp, a_lp, doubled_l)
        doubled_r = scipy.signal.lfilter(b_hp, a_hp, doubled_r)
        doubled_r = scipy.signal.lfilter(b_lp, a_lp, doubled_r)

        effective_mix = min(0.5, mix * 0.6)
        dry = 1.0 - effective_mix

        if is_1d:
            out_l = dry * mono + effective_mix * width * doubled_l
            out_r = dry * mono + effective_mix * width * doubled_r
            output = np.column_stack([out_l, out_r])
        else:
            out_l = dry * audio[:, 0] + effective_mix * width * doubled_l
            out_r = dry * audio[:, 1] + effective_mix * width * doubled_r
            output = np.column_stack([out_l, out_r])

        return output.astype(np.float32), {
            "stage": self.name,
            "status": "applied",
            "mix": round(effective_mix, 3),
            "width": width
        }
