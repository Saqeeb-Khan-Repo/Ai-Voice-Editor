import logging
import math
import numpy as np
import scipy.signal
import scipy.ndimage
from typing import Dict, Any, Tuple, Optional
from app.audio_engine.stages.base import PipelineStage

logger = logging.getLogger(__name__)

class NoiseReducerAdapter:
    """Base interface for interchangeable noise reduction backends."""
    def is_available(self) -> Tuple[bool, str]:
        raise NotImplementedError

    def reduce_noise(
        self,
        audio: np.ndarray,
        sample_rate: int,
        strength: float,
        mode: str = "balanced"
    ) -> np.ndarray:
        raise NotImplementedError


class DeepFilterNetAdapter(NoiseReducerAdapter):
    """
    Adapter for DeepFilterNet neural noise reduction.
    Safely wraps optional deepfilternet package.
    """
    def __init__(self):
        self._df_model = None
        self._df_state = None
        self._available = False
        self._reason = ""
        self._check_availability()

    def _check_availability(self):
        try:
            import df.enhance  # noqa: F401
            self._available = True
            self._reason = "DeepFilterNet neural model is installed and ready."
        except ImportError as e:
            self._available = False
            self._reason = f"DeepFilterNet not installed: {str(e)}"
        except Exception as e:
            self._available = False
            self._reason = f"DeepFilterNet initialization error: {str(e)}"

    def is_available(self) -> Tuple[bool, str]:
        return self._available, self._reason

    def reduce_noise(
        self,
        audio: np.ndarray,
        sample_rate: int,
        strength: float,
        mode: str = "balanced"
    ) -> np.ndarray:
        if not self._available:
            raise RuntimeError(f"DeepFilterNet is unavailable: {self._reason}")
        import df.enhance
        from df.enhance import init_df, enhance
        if self._df_model is None:
            self._df_model, self._df_state, _ = init_df()

        is_1d = audio.ndim == 1
        mono_audio = audio if is_1d else np.mean(audio, axis=1)
        enhanced = enhance(self._df_model, self._df_state, mono_audio)
        enhanced_np = enhanced.cpu().numpy()

        blended = (strength * enhanced_np) + ((1.0 - strength) * mono_audio)
        if not is_1d:
            return np.column_stack([blended, blended])
        return blended


class SpectralGatingAdapter(NoiseReducerAdapter):
    """
    Professional Studio-Grade Noise Reduction Engine.
    Engineered specifically for vocal recitation and Naats:
    - Multi-band STFT spectral subtraction with 2D time-frequency smoothing.
    - Eliminates stationary mic hiss, fan hum, and room acoustics without musical chirps.
    - Dynamic Voice Activity Downward Expander (Noise Gate) for total studio silence during pauses.
    - Configurable modes: subtle, balanced, aggressive, maximum studio clean.
    """
    def is_available(self) -> Tuple[bool, str]:
        return True, "Pure SciPy/NumPy Spectral Gating Engine (High Fidelity, Zero Artifacts)"

    def reduce_noise(
        self,
        audio: np.ndarray,
        sample_rate: int,
        strength: float,
        mode: str = "balanced"
    ) -> np.ndarray:
        if strength <= 0.01 or mode == "off":
            return audio.copy()

        is_1d = audio.ndim == 1
        channels = 1 if is_1d else audio.shape[1]
        out_channels = []

        for ch in range(channels):
            channel_data = audio if is_1d else audio[:, ch]
            processed_ch = self._process_single_channel(channel_data, sample_rate, strength, mode)
            out_channels.append(processed_ch)

        if is_1d:
            return out_channels[0]
        return np.column_stack(out_channels)

    def _process_single_channel(
        self,
        signal: np.ndarray,
        sample_rate: int,
        strength: float,
        mode: str
    ) -> np.ndarray:
        # STFT configuration optimized for human speech & vocal timbre
        n_fft = 2048
        hop_length = n_fft // 4
        win_length = n_fft
        window = scipy.signal.windows.hann(win_length)

        # STFT
        f, t, Zxx = scipy.signal.stft(
            signal,
            fs=sample_rate,
            window=window,
            nperseg=win_length,
            noverlap=win_length - hop_length,
            nfft=n_fft,
            boundary="zeros",
            padded=True
        )

        mag = np.abs(Zxx)

        # 1. Noise Profile Estimation
        # Find frames with lowest energy to capture ambient room tone and preamp noise
        frame_energies = np.sum(mag**2, axis=0)
        percentile_target = 25 if mode in ("aggressive", "maximum") else 20
        quiet_cutoff = np.percentile(frame_energies, percentile_target)
        quiet_indices = np.where(frame_energies <= quiet_cutoff)[0]

        if len(quiet_indices) >= 3:
            noise_profile = np.median(mag[:, quiet_indices], axis=1, keepdims=True)
        else:
            noise_profile = np.percentile(mag, 15, axis=1, keepdims=True)

        # 2. Over-subtraction and Spectral Floor Tuning
        if mode == "maximum":
            alpha = 2.4 + (strength * 3.0)
            beta = max(0.00005, (1.0 - strength) * 0.004)
        elif mode == "aggressive":
            alpha = 2.0 + (strength * 2.6)
            beta = max(0.0001, (1.0 - strength) * 0.008)
        elif mode == "subtle":
            alpha = 1.1 + (strength * 1.5)
            beta = max(0.005, (1.0 - strength) * 0.05)
        else:  # balanced
            alpha = 1.8 + (strength * 2.4)
            beta = max(0.0002, (1.0 - strength) * 0.01)

        # 3. Soft-Knee Spectral Gain Mask
        snr_est = np.maximum(mag / (noise_profile + 1e-10), 1e-6)
        gain_mask = np.maximum(1.0 - (alpha / (snr_est + 1.05)), beta)

        # 4. Two-Dimensional Smoothing (Time x Frequency)
        # Prevents watery musical chirping while keeping consonants crisp
        smoothed_mask = scipy.ndimage.uniform_filter(gain_mask, size=(3, 3))
        smoothed_mask = np.maximum(smoothed_mask, beta)

        # Apply mask directly to complex STFT (preserves exact phase without exp/angle overhead)
        processed_Zxx = Zxx * smoothed_mask

        # ISTFT
        _, recovered_signal = scipy.signal.istft(
            processed_Zxx,
            fs=sample_rate,
            window=window,
            nperseg=win_length,
            noverlap=win_length - hop_length,
            nfft=n_fft,
            boundary="zeros"
        )

        recovered_signal = recovered_signal[:len(signal)]
        if len(recovered_signal) < len(signal):
            recovered_signal = np.pad(recovered_signal, (0, len(signal) - len(recovered_signal)))

        # 5. Dynamic Downward Voice Activity Expander (Studio Noise Gate)
        # Specifically tuned for Quran, Naat & Nasheed vocal recitation:
        # - Wide soft-knee (14 dB) prevents sudden breath chopping
        # - Fast 6ms attack ensures consonants ("B", "T", "Qaf") are never cut
        # - Smooth 140ms release envelope preserves natural breath intakes and verse pauses
        if strength > 0.15:
            hop = 64
            ds_sr = sample_rate / hop
            n_samples = len(recovered_signal)
            n_frames = n_samples // hop
            if n_frames > 4:
                # Sub-sampled envelope calculation for instant, smooth response
                abs_sig = np.abs(recovered_signal[:n_frames * hop])
                frame_peaks = np.max(abs_sig.reshape(n_frames, hop), axis=1)
                env_db = 20.0 * np.log10(np.maximum(frame_peaks, 1e-6))

                # Mode-dependent threshold & floor
                if mode in ("maximum", "aggressive"):
                    gate_thresh = -42.0 + (strength * 12.0)
                    gate_floor = max(0.00005, (1.0 - strength) * 0.001)
                    knee_width = 11.0
                elif mode == "subtle":
                    gate_thresh = -48.0 + (strength * 8.0)
                    gate_floor = max(0.001, (1.0 - strength) * 0.02)
                    knee_width = 15.0
                else:  # balanced (default for vocal studio)
                    gate_thresh = -44.0 + (strength * 10.0)
                    gate_floor = max(0.0001, (1.0 - strength) * 0.003)
                    knee_width = 12.0

                raw_gain = np.ones(n_frames, dtype=np.float32)
                below_mask = env_db < gate_thresh
                if np.any(below_mask):
                    under_db = gate_thresh - env_db[below_mask]
                    attenuation = np.clip(under_db / knee_width, 0.0, 1.0)
                    raw_gain[below_mask] = (1.0 - attenuation) + (attenuation * gate_floor)

                # Asymmetric attack/release envelope follower:
                # Fast attack (6ms): instant opening on vocal articulation
                # Smooth release (140ms): natural breath intake preservation & room decay
                alpha_att = math.exp(-1.0 / (ds_sr * 0.006))
                alpha_rel = math.exp(-1.0 / (ds_sr * 0.140))

                smoothed_gain = np.empty(n_frames, dtype=np.float32)
                curr_g = 1.0
                for i in range(n_frames):
                    tgt = raw_gain[i]
                    if tgt > curr_g:
                        curr_g = (alpha_att * curr_g) + ((1.0 - alpha_att) * tgt)
                    else:
                        curr_g = (alpha_rel * curr_g) + ((1.0 - alpha_rel) * tgt)
                    smoothed_gain[i] = curr_g

                # Interpolate gain back to full audio length
                xp = np.arange(n_frames) * hop + (hop // 2)
                x_full = np.arange(n_samples)
                gain_full = np.interp(x_full, xp, smoothed_gain, left=smoothed_gain[0], right=smoothed_gain[-1]).astype(np.float32)
                recovered_signal = recovered_signal * gain_full

        return recovered_signal.astype(np.float32)


class NoiseReductionStage(PipelineStage):
    """
    Pipeline stage for intelligent noise reduction.
    Seamlessly dispatches to DeepFilterNet (if available) or Spectral Gating.
    """
    def __init__(self, preferred_backend: str = "auto"):
        super().__init__("noise_reduction")
        self.spectral_adapter = SpectralGatingAdapter()
        self.df_adapter = DeepFilterNetAdapter()
        self.preferred_backend = preferred_backend

    def process(
        self, audio: np.ndarray, sample_rate: int, config: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        self.validate_audio(audio)
        nr_cfg = config.get("noise_reduction", {})
        enabled = nr_cfg.get("enabled", True)
        strength = float(nr_cfg.get("strength", 0.65))
        mode = nr_cfg.get("mode", "balanced")

        if not enabled or strength <= 0.01 or mode == "off":
            return audio.copy(), {
                "stage": self.name,
                "status": "bypassed",
                "backend_used": "passthrough",
                "strength": 0.0,
                "mode": "off"
            }

        # Select backend
        df_ok, _ = self.df_adapter.is_available()
        if (self.preferred_backend == "deepfilternet" or self.preferred_backend == "auto") and df_ok:
            active_adapter = self.df_adapter
            backend_name = "DeepFilterNet (Neural)"
        else:
            active_adapter = self.spectral_adapter
            backend_name = "Spectral Gating (Pure DSP)"

        processed = active_adapter.reduce_noise(audio, sample_rate, strength, mode)
        return processed, {
            "stage": self.name,
            "status": "applied",
            "backend_used": backend_name,
            "strength": round(strength, 2),
            "mode": mode
        }
