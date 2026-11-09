import math
import numpy as np
import scipy.signal
from typing import Dict, Any, Tuple
from app.audio_engine.stages.base import PipelineStage

# Scale intervals in semitones relative to root (0)
SCALES = {
    "chromatic": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    "hijaz": [0, 1, 4, 5, 7, 8, 10],       # Maqam Hijaz (D, Eb, F#, G, A, Bb, C)
    "bayati": [0, 1, 3, 5, 7, 8, 10],      # Maqam Bayati
    "minor": [0, 2, 3, 5, 7, 8, 10],       # Natural Minor
    "major": [0, 2, 4, 5, 7, 9, 11],       # Major
}

class AutoTuneStage(PipelineStage):
    """
    Intelligent Vocal Pitch Correction & Auto-Tune Stage.
    Engineered for vocal recitation and Naat:
    - Autocorrelation fundamental frequency (F0) tracking.
    - Musical scale quantization (Chromatic, Maqam Hijaz, Maqam Bayati, Minor, Major).
    - Tunable retune speed and correction strength (subtle natural correction vs tight modern studio polish).
    """
    def __init__(self):
        super().__init__("autotune")

    def process(
        self, audio: np.ndarray, sample_rate: int, config: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        self.validate_audio(audio)
        tune_cfg = config.get("autotune", {})
        enabled = tune_cfg.get("enabled", False)
        strength = float(tune_cfg.get("strength", 0.0))
        scale_name = tune_cfg.get("scale", "chromatic").lower()

        if not enabled or strength <= 0.02:
            return audio.copy(), {
                "stage": self.name,
                "status": "bypassed",
                "strength": 0.0
            }

        is_1d = audio.ndim == 1
        mono = audio if is_1d else np.mean(audio, axis=1)

        scale_intervals = SCALES.get(scale_name, SCALES["chromatic"])

        # Process in overlapping 50ms chunks (hop 25ms)
        frame_len = int(sample_rate * 0.05)  # 50ms
        hop_len = frame_len // 2             # 25ms
        n_frames = (len(mono) - frame_len) // hop_len

        if n_frames <= 0:
            return audio.copy(), {"stage": self.name, "status": "bypassed"}

        # Window for overlap-add
        window = np.hanning(frame_len).astype(np.float32)
        output_mono = np.zeros_like(mono)
        norm_weights = np.zeros_like(mono)

        for i in range(n_frames):
            idx = i * hop_len
            frame = mono[idx : idx + frame_len]
            # Detect pitch
            pitch_hz = self._detect_pitch_autocorr(frame, sample_rate)

            shift_semitones = 0.0
            if pitch_hz > 70.0 and pitch_hz < 650.0:
                # Convert Hz to MIDI note
                midi_note = 69.0 + 12.0 * math.log2(pitch_hz / 440.0)
                # Find nearest target note in chosen scale
                target_midi = self._snap_to_scale(midi_note, scale_intervals)
                semitone_delta = target_midi - midi_note
                # Apply strength scaling
                shift_semitones = semitone_delta * strength

            if abs(shift_semitones) > 0.05:
                processed_frame = self._pitch_shift_frame(frame, shift_semitones)
            else:
                processed_frame = frame

            # Overlap-add
            output_mono[idx : idx + frame_len] += processed_frame * window
            norm_weights[idx : idx + frame_len] += window

        # Normalize overlap-add
        nonzero_mask = norm_weights > 1e-4
        output_mono[nonzero_mask] /= norm_weights[nonzero_mask]

        # Blend dry and tuned based on strength
        blended = (strength * output_mono) + ((1.0 - strength) * mono)

        if is_1d:
            res = blended.astype(np.float32)
        else:
            # Reconstruct stereo
            res = np.zeros_like(audio)
            for ch in range(audio.shape[1]):
                res[:, ch] = (strength * output_mono) + ((1.0 - strength) * audio[:, ch])

        return res.astype(np.float32), {
            "stage": self.name,
            "status": "applied",
            "scale": scale_name,
            "strength": strength,
        }

    @staticmethod
    def _detect_pitch_autocorr(frame: np.ndarray, sr: int) -> float:
        """Autocorrelation fundamental pitch detector for vocal range (70Hz - 600Hz)."""
        if np.max(np.abs(frame)) < 0.015:
            return 0.0
        corr = scipy.signal.correlate(frame, frame, mode="full")
        corr = corr[len(corr) // 2 :]

        min_lag = int(sr / 600)  # max 600 Hz
        max_lag = int(sr / 70)   # min 70 Hz

        if max_lag >= len(corr):
            return 0.0

        peak_lag = min_lag + int(np.argmax(corr[min_lag:max_lag]))
        if corr[peak_lag] > 0.35 * corr[0]:
            return float(sr / peak_lag)
        return 0.0

    @staticmethod
    def _snap_to_scale(midi_pitch: float, scale_intervals: list) -> float:
        """Snaps floating-point MIDI pitch to the closest note in the musical scale."""
        note_in_octave = midi_pitch % 12.0
        octave_base = math.floor(midi_pitch / 12.0) * 12.0

        best_interval = scale_intervals[0]
        min_dist = 999.0

        for interval in scale_intervals:
            dist = abs(note_in_octave - interval)
            if dist < min_dist:
                min_dist = dist
                best_interval = interval

            # Check octave wrapping
            dist_wrap = abs(note_in_octave - (interval + 12))
            if dist_wrap < min_dist:
                min_dist = dist_wrap
                best_interval = interval + 12

        return octave_base + best_interval

    @staticmethod
    def _pitch_shift_frame(frame: np.ndarray, n_semitones: float) -> np.ndarray:
        """Pitch shifts frame using resampling and time-interpolation."""
        factor = 2.0 ** (n_semitones / 12.0)
        n_orig = len(frame)
        n_resampled = max(8, int(n_orig / factor))

        resampled = scipy.signal.resample(frame, n_resampled)
        orig_t = np.linspace(0, 1, n_orig)
        res_t = np.linspace(0, 1, len(resampled))
        shifted = np.interp(orig_t, res_t, resampled).astype(np.float32)
        return shifted
