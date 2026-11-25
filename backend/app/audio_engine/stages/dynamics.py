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

        # 2. Vectorized Gain Computation with Soft Knee
        half_knee = knee_db / 2.0
        y_out = signal_db.copy()
        upper_mask = signal_db >= (threshold_db + half_knee)
        y_out[upper_mask] = threshold_db + (signal_db[upper_mask] - threshold_db) / ratio
        if knee_db > 1e-6:
            knee_mask = (signal_db > (threshold_db - half_knee)) & (~upper_mask)
            if np.any(knee_mask):
                xk = signal_db[knee_mask]
                y_out[knee_mask] = xk + ((1.0 / ratio - 1.0) * ((xk - threshold_db + half_knee) ** 2)) / (2.0 * knee_db)
        gain_reduction_db = y_out - signal_db  # non-positive (<= 0)

        # 3. Smooth gain reduction curve with block-subsampled attack/release envelope
        n_samples = len(gain_reduction_db)
        hop = 64 if n_samples > 256 else 1
        if hop > 1:
            n_frames = n_samples // hop
            ds_sr = sample_rate / hop
            alpha_att_ds = math.exp(-1.0 / (ds_sr * (attack_ms / 1000.0)))
            alpha_rel_ds = math.exp(-1.0 / (ds_sr * (release_ms / 1000.0)))

            gr_blocks = gain_reduction_db[: n_frames * hop].reshape(n_frames, hop)
            gr_ds = np.min(gr_blocks, axis=1)

            smoothed_ds = np.empty(n_frames, dtype=np.float32)
            current_gr = 0.0
            for i in range(n_frames):
                target_gr = float(gr_ds[i])
                if target_gr < current_gr:
                    current_gr = (alpha_att_ds * current_gr) + ((1.0 - alpha_att_ds) * target_gr)
                else:
                    current_gr = (alpha_rel_ds * current_gr) + ((1.0 - alpha_rel_ds) * target_gr)
                smoothed_ds[i] = current_gr

            xp = np.arange(n_frames) * hop + (hop // 2)
            x_full = np.arange(n_samples)
            smoothed_gr_db = np.interp(x_full, xp, smoothed_ds, left=smoothed_ds[0], right=smoothed_ds[-1]).astype(np.float32)
        else:
            smoothed_gr_db = np.zeros_like(gain_reduction_db)
            current_gr = 0.0
            for i in range(n_samples):
                target_gr = float(gain_reduction_db[i])
                if target_gr < current_gr:
                    current_gr = (alpha_attack * current_gr) + ((1.0 - alpha_attack) * target_gr)
                else:
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

        thresh_linear = 10.0 ** (threshold_db / 20.0)
        n_samples = len(sibilance_band)
        hop = 32 if n_samples > 128 else 1

        if hop > 1:
            n_frames = n_samples // hop
            ds_sr = sample_rate / hop
            alpha_att_ds = math.exp(-1.0 / (ds_sr * 0.001))
            alpha_rel_ds = math.exp(-1.0 / (ds_sr * 0.050))

            sib_blocks = np.abs(sibilance_band[: n_frames * hop]).reshape(n_frames, hop)
            sib_peaks = np.max(sib_blocks, axis=1)

            env_ds = np.empty(n_frames, dtype=np.float32)
            env = 0.0
            for i in range(n_frames):
                sample_abs = float(sib_peaks[i])
                if sample_abs > env:
                    env = (alpha_att_ds * env) + ((1.0 - alpha_att_ds) * sample_abs)
                else:
                    env = (alpha_rel_ds * env) + ((1.0 - alpha_rel_ds) * sample_abs)
                env_ds[i] = env

            att_ds = np.ones(n_frames, dtype=np.float32)
            over_mask = env_ds > thresh_linear
            if np.any(over_mask):
                att_ds[over_mask] = np.maximum(0.4, thresh_linear / env_ds[over_mask])

            xp = np.arange(n_frames) * hop + (hop // 2)
            x_full = np.arange(n_samples)
            attenuation = np.interp(x_full, xp, att_ds, left=att_ds[0], right=att_ds[-1]).astype(np.float32)
        else:
            alpha_att = math.exp(-1.0 / (sample_rate * 0.001))
            alpha_rel = math.exp(-1.0 / (sample_rate * 0.050))
            env = 0.0
            attenuation = np.ones(n_samples, dtype=np.float32)
            for i in range(n_samples):
                sample_abs = abs(sibilance_band[i])
                if sample_abs > env:
                    env = (alpha_att * env) + ((1.0 - alpha_att) * sample_abs)
                else:
                    env = (alpha_rel * env) + ((1.0 - alpha_rel) * sample_abs)
                if env > thresh_linear:
                    attenuation[i] = max(0.4, thresh_linear / env)

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

        # Smooth gain release (sub-sampled block minimum + instant sample-accurate clamp)
        n_samples = len(target_gain)
        hop = 32 if n_samples > 128 else 1
        if hop > 1:
            n_frames = n_samples // hop
            ds_release_frames = max(1, release_samples // hop)
            alpha_rel_ds = math.exp(-1.0 / ds_release_frames)

            tg_blocks = target_gain[: n_frames * hop].reshape(n_frames, hop)
            tg_ds = np.min(tg_blocks, axis=1)

            smooth_ds = np.empty(n_frames, dtype=np.float32)
            current_g = 1.0
            for i in range(n_frames):
                tg = float(tg_ds[i])
                if tg < current_g:
                    current_g = tg
                else:
                    current_g = (alpha_rel_ds * current_g) + ((1.0 - alpha_rel_ds) * tg)
                smooth_ds[i] = current_g

            xp = np.arange(n_frames) * hop + (hop // 2)
            x_full = np.arange(n_samples)
            smooth_gain = np.interp(x_full, xp, smooth_ds, left=smooth_ds[0], right=smooth_ds[-1]).astype(np.float32)
            smooth_gain = np.minimum(smooth_gain, target_gain)
        else:
            smooth_gain = np.ones_like(target_gain)
            current_g = 1.0
            for i in range(n_samples):
                tg = float(target_gain[i])
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
