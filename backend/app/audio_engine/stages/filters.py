import math
import numpy as np
import scipy.signal
from typing import Dict, Any, Tuple
from app.audio_engine.stages.base import PipelineStage

class HighPassFilterStage(PipelineStage):
    """
    Stage 4: High-pass filtering.
    Removes DC offset, subsonic rumble, and handling thump.
    Uses 2nd order Butterworth high-pass filter.
    """
    def __init__(self):
        super().__init__("high_pass_filter")

    def process(
        self, audio: np.ndarray, sample_rate: int, config: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        self.validate_audio(audio)
        hp_cfg = config.get("high_pass", {})
        if not hp_cfg.get("enabled", True):
            return audio.copy(), {"stage": self.name, "status": "bypassed"}

        cutoff_hz = float(hp_cfg.get("cutoff_hz", 60.0))
        order = int(hp_cfg.get("order", 2))

        # Clamp cutoff to safe Nyquist limit
        nyquist = sample_rate * 0.5
        cutoff_hz = min(max(20.0, cutoff_hz), nyquist * 0.9)
        norm_cutoff = cutoff_hz / nyquist

        sos = scipy.signal.butter(order, norm_cutoff, btype="highpass", output="sos")

        is_1d = audio.ndim == 1
        if is_1d:
            filtered = scipy.signal.sosfilt(sos, audio)
        else:
            filtered = np.zeros_like(audio)
            for ch in range(audio.shape[1]):
                filtered[:, ch] = scipy.signal.sosfilt(sos, audio[:, ch])

        return filtered.astype(np.float32), {
            "stage": self.name,
            "status": "applied",
            "cutoff_hz": cutoff_hz,
            "order": order
        }


class EqualizerStage(PipelineStage):
    """
    Stage 5: Conservative automatic vocal equalization.
    Implements RBJ Audio EQ Cookbook biquad filters:
    - Low-mid parametric bell filter (anti-boxiness / anti-mud)
    - High-mid parametric bell filter (diction & intelligibility)
    - High-frequency shelving filter (air & vocal openness)
    """
    def __init__(self):
        super().__init__("equalizer")

    def process(
        self, audio: np.ndarray, sample_rate: int, config: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        self.validate_audio(audio)
        eq_cfg = config.get("equalizer", {})
        if not eq_cfg.get("enabled", True):
            return audio.copy(), {"stage": self.name, "status": "bypassed"}

        mud_gain = float(eq_cfg.get("mud_cut_gain_db", -1.0))
        mud_freq = float(eq_cfg.get("mud_cut_freq_hz", 300.0))
        
        pres_gain = float(eq_cfg.get("presence_boost_gain_db", 1.0))
        pres_freq = float(eq_cfg.get("presence_freq_hz", 3200.0))
        
        air_gain = float(eq_cfg.get("air_shelf_gain_db", 1.5))
        air_freq = float(eq_cfg.get("air_shelf_freq_hz", 10000.0))

        processed = audio.copy()

        # 1. Mud Notch / Cut (Peaking EQ)
        if abs(mud_gain) > 0.1:
            processed = self._apply_peaking_eq(processed, sample_rate, mud_freq, mud_gain, q=1.2)

        # 2. Presence / Intelligibility Bell (Peaking EQ)
        if abs(pres_gain) > 0.1:
            processed = self._apply_peaking_eq(processed, sample_rate, pres_freq, pres_gain, q=1.0)

        # 3. High Air Shelf
        if abs(air_gain) > 0.1:
            processed = self._apply_high_shelf(processed, sample_rate, air_freq, air_gain)

        return processed.astype(np.float32), {
            "stage": self.name,
            "status": "applied",
            "mud_gain_db": mud_gain,
            "presence_gain_db": pres_gain,
            "air_gain_db": air_gain
        }

    @staticmethod
    def _apply_peaking_eq(audio: np.ndarray, sr: int, f0: float, gain_db: float, q: float = 1.0) -> np.ndarray:
        if f0 >= sr * 0.48:
            return audio
        w0 = 2.0 * math.pi * (f0 / sr)
        alpha = math.sin(w0) / (2.0 * max(q, 0.1))
        A = 10.0 ** (gain_db / 40.0)

        b0 = 1.0 + (alpha * A)
        b1 = -2.0 * math.cos(w0)
        b2 = 1.0 - (alpha * A)
        a0 = 1.0 + (alpha / A)
        a1 = -2.0 * math.cos(w0)
        a2 = 1.0 - (alpha / A)

        b = np.array([b0 / a0, b1 / a0, b2 / a0], dtype=np.float64)
        a = np.array([1.0, a1 / a0, a2 / a0], dtype=np.float64)

        if audio.ndim == 1:
            return scipy.signal.lfilter(b, a, audio)
        out = np.zeros_like(audio)
        for ch in range(audio.shape[1]):
            out[:, ch] = scipy.signal.lfilter(b, a, audio[:, ch])
        return out

    @staticmethod
    def _apply_high_shelf(audio: np.ndarray, sr: int, f0: float, gain_db: float) -> np.ndarray:
        if f0 >= sr * 0.48:
            return audio
        A = 10.0 ** (gain_db / 40.0)
        w0 = 2.0 * math.pi * (f0 / sr)
        cos_w0 = math.cos(w0)
        sin_w0 = math.sin(w0)
        alpha = sin_w0 / 2.0 * math.sqrt(2.0)

        b0 = A * ((A + 1.0) + ((A - 1.0) * cos_w0) + (2.0 * math.sqrt(A) * alpha))
        b1 = -2.0 * A * ((A - 1.0) + ((A + 1.0) * cos_w0))
        b2 = A * ((A + 1.0) + ((A - 1.0) * cos_w0) - (2.0 * math.sqrt(A) * alpha))
        a0 = (A + 1.0) - ((A - 1.0) * cos_w0) + (2.0 * math.sqrt(A) * alpha)
        a1 = 2.0 * ((A - 1.0) - ((A + 1.0) * cos_w0))
        a2 = (A + 1.0) - ((A - 1.0) * cos_w0) - (2.0 * math.sqrt(A) * alpha)

        b = np.array([b0 / a0, b1 / a0, b2 / a0], dtype=np.float64)
        a = np.array([1.0, a1 / a0, a2 / a0], dtype=np.float64)

        if audio.ndim == 1:
            return scipy.signal.lfilter(b, a, audio)
        out = np.zeros_like(audio)
        for ch in range(audio.shape[1]):
            out[:, ch] = scipy.signal.lfilter(b, a, audio[:, ch])
        return out
