import math
import numpy as np
import scipy.signal
from typing import Dict, Any, Tuple
from app.audio_engine.stages.base import PipelineStage

class EchoDelayStage(PipelineStage):
    """
    Studio Vocal Echo & Delay Stage.
    Engineered specifically for spiritual recitations, Naats, and Qawwali vocals:
    - Warm analog-style tempo delay.
    - Low-pass damping inside the feedback loop to soften repeats.
    - Stereo ping-pong offset for immersive space.
    - Configurable delay time, feedback repeats, and wet mix.
    """
    def __init__(self):
        super().__init__("echo_delay")

    def process(
        self, audio: np.ndarray, sample_rate: int, config: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        self.validate_audio(audio)
        echo_cfg = config.get("echo", {})
        enabled = echo_cfg.get("enabled", False)
        wet = float(echo_cfg.get("wet", 0.0))
        delay_time_ms = float(echo_cfg.get("delay_time_ms", 240.0))
        feedback = float(echo_cfg.get("feedback", 0.25))
        damping = float(echo_cfg.get("damping", 0.45))  # High-cut damping

        if not enabled or wet <= 0.01:
            return audio.copy(), {
                "stage": self.name,
                "status": "bypassed",
                "wet": 0.0
            }

        is_1d = audio.ndim == 1
        mono = audio if is_1d else np.mean(audio, axis=1)

        delay_samples = int(sample_rate * (delay_time_ms / 1000.0))
        if delay_samples <= 0 or delay_samples >= len(mono):
            return audio.copy(), {"stage": self.name, "status": "bypassed"}

        # Ping-pong delay buffers for left and right
        delay_samples_l = delay_samples
        delay_samples_r = int(delay_samples * 1.15)  # slight offset for stereo dimension

        echo_l = self._apply_delay_loop(mono, delay_samples_l, feedback, damping)
        echo_r = self._apply_delay_loop(mono, delay_samples_r, feedback, damping)

        # Soft high-cut at 3500 Hz on echo return to keep vocal upfront
        nyquist = sample_rate * 0.5
        b_cut, a_cut = scipy.signal.butter(1, min(3500.0, nyquist * 0.8) / nyquist, btype="low")
        echo_l = scipy.signal.lfilter(b_cut, a_cut, echo_l)
        echo_r = scipy.signal.lfilter(b_cut, a_cut, echo_r)

        dry = 1.0 - (wet * 0.3)

        if is_1d:
            # Mono mix
            wet_mono = (echo_l + echo_r) * 0.5
            output = (dry * audio) + (wet * wet_mono)
        else:
            out_l = (dry * audio[:, 0]) + (wet * echo_l)
            out_r = (dry * audio[:, 1]) + (wet * echo_r)
            output = np.column_stack([out_l, out_r])

        return output.astype(np.float32), {
            "stage": self.name,
            "status": "applied",
            "wet": wet,
            "delay_time_ms": delay_time_ms,
            "feedback": feedback,
        }

    @staticmethod
    def _apply_delay_loop(signal: np.ndarray, delay: int, feedback: float, damping: float) -> np.ndarray:
        out = np.zeros_like(signal)
        n = len(signal)
        feedback = min(0.65, max(0.05, feedback))

        filter_mem = 0.0
        d_inv = 1.0 - damping

        for i in range(delay, n):
            delayed_sample = out[i - delay] + signal[i - delay]
            # 1-pole lowpass damping
            filter_mem = (delayed_sample * d_inv) + (filter_mem * damping)
            out[i] = feedback * filter_mem

        return out
