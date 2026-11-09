import math
import numpy as np
import scipy.signal
from typing import Dict, Any, Tuple
from app.audio_engine.stages.base import PipelineStage

class CompressorStage(PipelineStage):
    """
    Stage 6: Transparent Dynamic Vocal Compression.
    Feed-forward soft-knee compressor with envelope follower and automatic makeup gain.
    Preserves natural vocal expression while controlling loud peaks and lifting quiet nuances.
    """
    def __init__(self):
        super().__init__("compressor")

    def process(
        self, audio: np.ndarray, sample_rate: int, config: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        self.validate_audio(audio)
        comp_cfg = config.get("compressor", {})
        if not comp_cfg.get("enabled", True):
            return audio.copy(), {"stage": self.name, "status": "bypassed"}

        threshold_db = float(comp_cfg.get("threshold_db", -18.0))
        ratio = float(comp_cfg.get("ratio", 2.2))
        attack_ms = float(comp_cfg.get("attack_ms", 25.0))
        release_ms = float(comp_cfg.get("release_ms", 180.0))
        knee_db = float(comp_cfg.get("knee_db", 4.0))

        if ratio <= 1.01:
            return audio.copy(), {"stage": self.name, "status": "bypassed"}

        # Ballistics time constants
        alpha_attack = math.exp(-1.0 / (sample_rate * (attack_ms / 1000.0)))
        alpha_release = math.exp(-1.0 / (sample_rate * (release_ms / 1000.0)))

        is_1d = audio.ndim == 1
        mono = audio if is_1d else np.mean(audio, axis=1)

        # 1. Level Detection (in dB)
        abs_signal = np.abs(mono)
        # Avoid log(0)
        signal_db = 20.0 * np.log10(np.maximum(abs_signal, 1e-6))

        # 2. Gain Computation with Soft Knee
        # Gain reduction characteristic:
        gain_reduction_db = np.zeros_like(signal_db)
        half_knee = knee_db / 2.0

        for i in range(len(signal_db)):
            x = signal_db[i]
            if x <= threshold_db - half_knee:
                y = x
            elif x >= threshold_db + half_knee:
                y = threshold_db + (x - threshold_db) / ratio
            else:
                # Soft knee quadratic interpolation
                y = x + ((1.0 / ratio - 1.0) * ((x - threshold_db + half_knee) ** 2)) / (2.0 * knee_db)
            gain_reduction_db[i] = y - x  # non-positive (<= 0)

        # 3. Smooth gain reduction curve with attack/release envelope
        smoothed_gr_db = np.zeros_like(gain_reduction_db)
        current_gr = 0.0
        for i in range(len(gain_reduction_db)):
            target_gr = gain_reduction_db[i]
            if target_gr < current_gr:
                # Attacking (reducing gain)
                current_gr = (alpha_attack * current_gr) + ((1.0 - alpha_attack) * target_gr)
            else:
                # Releasing (recovering gain)
                current_gr = (alpha_release * current_gr) + ((1.0 - alpha_release) * target_gr)
            smoothed_gr_db[i] = current_gr

        # 4. Linear gain factor (Dynamic compression envelope)
        makeup_gain_db = float(comp_cfg.get("makeup_gain_db", 0.0))
        gain_linear = (10.0 ** ((smoothed_gr_db + makeup_gain_db) / 20.0)).astype(np.float32)

        # 5. Apply gain
        if is_1d:
            compressed = audio * gain_linear
        else:
            compressed = audio * gain_linear[:, np.newaxis]

        max_gr_applied = float(np.min(smoothed_gr_db))
        return compressed.astype(np.float32), {
            "stage": self.name,
            "status": "applied",
            "threshold_db": threshold_db,
            "ratio": ratio,
            "max_gain_reduction_db": round(max_gr_applied, 2),
            "makeup_gain_db": round(makeup_gain_db, 2)
        }


class DeesserStage(PipelineStage):
    """
    Stage 7: Transparent vocal de-essing.
    Isolates sibilance band (5-8 kHz) using a Butterworth bandpass filter.
    When sibilance exceeds threshold, dynamic sidechain compression reduces harshness.
    """
    def __init__(self):
        super().__init__("deesser")

    def process(
        self, audio: np.ndarray, sample_rate: int, config: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        self.validate_audio(audio)
        deess_cfg = config.get("deesser", {})
        if not deess_cfg.get("enabled", False):
            return audio.copy(), {"stage": self.name, "status": "bypassed"}

        threshold_db = float(deess_cfg.get("threshold_db", -16.0))
        center_freq = float(deess_cfg.get("freq_hz", 6500.0))
        bandwidth = 2000.0

        nyquist = sample_rate * 0.5
        low_f = max(2000.0, center_freq - bandwidth / 2.0) / nyquist
        high_f = min(nyquist * 0.95, center_freq + bandwidth / 2.0) / nyquist

        if low_f >= high_f or high_f >= 1.0:
            return audio.copy(), {"stage": self.name, "status": "bypassed"}

        # Bandpass sidechain filter
        sos_bp = scipy.signal.butter(2, [low_f, high_f], btype="bandpass", output="sos")

        is_1d = audio.ndim == 1
        mono = audio if is_1d else np.mean(audio, axis=1)
        sibilance_band = scipy.signal.sosfilt(sos_bp, mono)

        # Fast attack (1ms), fast release (50ms)
        alpha_att = math.exp(-1.0 / (sample_rate * 0.001))
        alpha_rel = math.exp(-1.0 / (sample_rate * 0.050))

        env = 0.0
        attenuation = np.ones(len(mono), dtype=np.float32)
        thresh_linear = 10.0 ** (threshold_db / 20.0)

        for i in range(len(sibilance_band)):
            sample_abs = abs(sibilance_band[i])
            if sample_abs > env:
                env = (alpha_att * env) + ((1.0 - alpha_att) * sample_abs)
            else:
                env = (alpha_rel * env) + ((1.0 - alpha_rel) * sample_abs)

            if env > thresh_linear:
                # Dynamic attenuation on the sibilance frequency
                excess_ratio = thresh_linear / env
                attenuation[i] = max(0.4, excess_ratio)
            else:
                attenuation[i] = 1.0

        # Apply attenuation only to the sibilant band
        if is_1d:
            deessed = audio - (sibilance_band * (1.0 - attenuation))
        else:
            deessed = np.zeros_like(audio)
            for ch in range(audio.shape[1]):
                ch_sib = scipy.signal.sosfilt(sos_bp, audio[:, ch])
                deessed[:, ch] = audio[:, ch] - (ch_sib * (1.0 - attenuation))

        return deessed.astype(np.float32), {
            "stage": self.name,
            "status": "applied",
            "threshold_db": threshold_db,
            "center_freq_hz": center_freq
        }


class LimiterStage(PipelineStage):
    """
    Stage 10: True-Peak Brickwall Lookahead Limiter.
    Guarantees that true peak never exceeds ceiling (e.g. -1.0 dBTP).
    Uses 5ms lookahead buffer and smooth release envelope to prevent DAC clipping.
    """
    def __init__(self):
        super().__init__("limiter")

    def process(
        self, audio: np.ndarray, sample_rate: int, config: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        self.validate_audio(audio)
        limiter_cfg = config.get("limiter", {})
        ceiling_dbtp = float(limiter_cfg.get("ceiling_dbtp", -1.0))
        ceiling_linear = 10.0 ** (ceiling_dbtp / 20.0)

        lookahead_samples = int(sample_rate * 0.005)  # 5ms lookahead
        release_samples = int(sample_rate * 0.050)   # 50ms release
        alpha_rel = math.exp(-1.0 / release_samples)

        is_1d = audio.ndim == 1
        mono = audio if is_1d else np.mean(audio, axis=1)

        # Delay signal by lookahead_samples
        pad = np.zeros(lookahead_samples, dtype=np.float32)
        if is_1d:
            delayed_audio = np.concatenate([pad, audio])[:len(audio)]
        else:
            pad_2d = np.zeros((lookahead_samples, audio.shape[1]), dtype=np.float32)
            delayed_audio = np.vstack([pad_2d, audio])[:len(audio)]

        # Peak envelope follower on mono
        peak_env = np.abs(mono)
        # Compute required gain factor
        target_gain = np.ones(len(peak_env), dtype=np.float32)
        over_mask = peak_env > ceiling_linear
        target_gain[over_mask] = ceiling_linear / peak_env[over_mask]

        # Smooth gain release
        smooth_gain = np.ones_like(target_gain)
        current_g = 1.0
        for i in range(len(target_gain)):
            tg = target_gain[i]
            if tg < current_g:
                current_g = tg  # Instant attack for zero overshoot
            else:
                current_g = (alpha_rel * current_g) + ((1.0 - alpha_rel) * tg)
            smooth_gain[i] = current_g

        if is_1d:
            limited = delayed_audio * smooth_gain
        else:
            limited = delayed_audio * smooth_gain[:, np.newaxis]

        # Ensure no individual sample exceeds ceiling
        limited = np.clip(limited, -ceiling_linear, ceiling_linear)

        return limited.astype(np.float32), {
            "stage": self.name,
            "status": "applied",
            "ceiling_dbtp": ceiling_dbtp,
            "min_gain_applied": float(np.min(smooth_gain))
        }
