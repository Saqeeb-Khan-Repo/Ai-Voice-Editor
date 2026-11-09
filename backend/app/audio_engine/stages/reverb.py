import math
import numpy as np
import scipy.signal
from typing import Dict, Any, Tuple
from app.audio_engine.stages.base import PipelineStage

class NaturalReverbStage(PipelineStage):
    """
    Stage 8: Natural Acoustic Reverb.
    Engineered specifically for vocal recitation and Naat:
    - Pre-delay to preserve vocal intimacy and clear consonant articulation.
    - Schroeder/Moorer algorithmic reverberator with prime-spaced comb filters.
    - Low-pass damping inside feedback loops to avoid metallic harshness.
    - Series allpass diffusion stages for lush natural density.
    - Stereo field widening while maintaining strict mono compatibility.
    """
    def __init__(self):
        super().__init__("natural_reverb")

    def process(
        self, audio: np.ndarray, sample_rate: int, config: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        self.validate_audio(audio)
        rev_cfg = config.get("reverb", {})
        if not rev_cfg.get("enabled", True):
            return audio.copy(), {"stage": self.name, "status": "bypassed"}

        wet = float(rev_cfg.get("wet", 0.08))
        dry = float(rev_cfg.get("dry", 0.95))
        decay_time = float(rev_cfg.get("decay_time_seconds", 1.2))
        pre_delay_ms = float(rev_cfg.get("pre_delay_ms", 25.0))
        damping = float(rev_cfg.get("damping", 0.4))

        if wet <= 0.005:
            return audio.copy(), {"stage": self.name, "status": "bypassed"}

        is_1d = audio.ndim == 1
        mono_input = audio if is_1d else np.mean(audio, axis=1)

        # 1. Pre-delay buffer
        pre_delay_samples = int(sample_rate * (pre_delay_ms / 1000.0))
        delayed_signal = np.pad(mono_input, (pre_delay_samples, 0))[:len(mono_input)]

        # 2. Parallel Feedback Comb Filters with coprime delays
        # Delay lengths in milliseconds scaled to sample rate
        comb_delays_ms = [29.7, 37.1, 41.1, 43.7]
        comb_outputs_l = []
        comb_outputs_r = []

        for idx, delay_ms in enumerate(comb_delays_ms):
            d_samples = int(sample_rate * (delay_ms / 1000.0))
            # Feedback gain calculated from decay time (T60)
            # gain = 10^(-3 * delay / decay_time)
            feedback = 10.0 ** (-3.0 * (delay_ms / 1000.0) / max(0.2, decay_time))
            feedback = min(0.92, feedback)

            # Comb filter with damping
            comb_out = self._filtered_comb(delayed_signal, d_samples, feedback, damping)
            
            # Stereo spread: alternate phase/comb distribution
            if idx % 2 == 0:
                comb_outputs_l.append(comb_out)
                comb_outputs_r.append(comb_out * 0.85)
            else:
                comb_outputs_l.append(comb_out * 0.85)
                comb_outputs_r.append(comb_out)

        wet_l = np.sum(comb_outputs_l, axis=0) * 0.25
        wet_r = np.sum(comb_outputs_r, axis=0) * 0.25

        # 3. Series Allpass Filters for spatial diffusion
        allpass_delays_ms = [5.0, 1.7]
        for ap_ms in allpass_delays_ms:
            ap_samples = int(sample_rate * (ap_ms / 1000.0))
            wet_l = self._allpass_filter(wet_l, ap_samples, 0.5)
            wet_r = self._allpass_filter(wet_r, ap_samples + 2, 0.5)

        # 4. Soft High-Cut on Reverb Tail (gentle lowpass at 5.5 kHz)
        nyquist = sample_rate * 0.5
        b_lp, a_lp = scipy.signal.butter(1, min(5500.0, nyquist * 0.8) / nyquist, btype="low")
        wet_l = scipy.signal.lfilter(b_lp, a_lp, wet_l)
        wet_r = scipy.signal.lfilter(b_lp, a_lp, wet_r)

        # 5. Blend Dry and Wet
        if is_1d:
            # Mono output
            wet_mono = (wet_l + wet_r) * 0.5
            output = (dry * audio) + (wet * wet_mono)
        else:
            # Stereo output
            out_l = (dry * audio[:, 0]) + (wet * wet_l)
            out_r = (dry * audio[:, 1]) + (wet * wet_r)
            output = np.column_stack([out_l, out_r])

        return output.astype(np.float32), {
            "stage": self.name,
            "status": "applied",
            "wet": wet,
            "decay_time_seconds": decay_time,
            "pre_delay_ms": pre_delay_ms
        }

    @staticmethod
    def _filtered_comb(signal: np.ndarray, delay: int, feedback: float, damping: float) -> np.ndarray:
        """
        Feedback comb filter with 1-pole lowpass damping inside feedback loop.
        y[n] = x[n] + feedback * ( (1-d)*buffer[n-delay] + d*buffer_prev )
        """
        out = np.zeros_like(signal)
        n = len(signal)
        if delay >= n or delay <= 0:
            return signal * feedback

        # Fast vectorization / loop
        filter_store = 0.0
        d_inv = 1.0 - damping

        for i in range(n):
            delayed_sample = out[i - delay] if i >= delay else 0.0
            filter_store = (delayed_sample * d_inv) + (filter_store * damping)
            out[i] = signal[i] + (feedback * filter_store)

        return out

    @staticmethod
    def _allpass_filter(signal: np.ndarray, delay: int, gain: float) -> np.ndarray:
        """
        Schroeder all-pass filter for diffusion.
        y[n] = -g*x[n] + x[n-delay] + g*y[n-delay]
        """
        out = np.zeros_like(signal)
        n = len(signal)
        if delay >= n or delay <= 0:
            return signal

        for i in range(n):
            x_del = signal[i - delay] if i >= delay else 0.0
            y_del = out[i - delay] if i >= delay else 0.0
            out[i] = -gain * signal[i] + x_del + gain * y_del

        return out
