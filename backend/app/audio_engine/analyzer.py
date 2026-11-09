import math
import numpy as np
import scipy.signal
import soundfile as sf
import pyloudnorm as pyln
from typing import Dict, Any, List, Optional, Tuple

class AudioAnalyzer:
    """
    Independent audio analysis engine.
    Measures duration, sample rate, channels, peak amplitude, RMS, crest factor,
    integrated LUFS, true peak dBTP, clipping, silence regions, frequency distribution,
    and background noise characteristics.
    """

    @staticmethod
    def load_audio(file_path: str) -> Tuple[np.ndarray, int]:
        """
        Loads audio file as float32 in range [-1.0, 1.0].
        Returns:
            audio: np.ndarray shape (samples,) for mono or (samples, channels) for stereo
            sample_rate: int
        """
        audio, sr = sf.read(file_path, dtype="float32", always_2d=False)
        return audio, sr

    @classmethod
    def analyze(cls, audio: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """
        Performs exhaustive objective audio analysis on numpy audio array.
        """
        # Ensure float32 and shape
        if audio.ndim == 1:
            samples = len(audio)
            channels = 1
            audio_2d = audio[:, np.newaxis]
        else:
            samples, channels = audio.shape
            audio_2d = audio

        duration_seconds = float(samples / sample_rate) if sample_rate > 0 else 0.0

        if samples == 0 or duration_seconds == 0:
            return cls._empty_report(sample_rate, channels)

        # 1. Peak Amplitude and True Peak (dBFS & dBTP)
        max_abs = float(np.max(np.abs(audio)))
        peak_amplitude_dbfs = 20.0 * math.log10(max(max_abs, 1e-9))
        
        # True Peak with 4x polyphase oversampling
        true_peak_dbtp = cls._calculate_true_peak(audio, sample_rate)

        # 2. RMS and Crest Factor
        rms_val = float(np.sqrt(np.mean(np.square(audio))))
        rms_dbfs = 20.0 * math.log10(max(rms_val, 1e-9))
        crest_factor_db = peak_amplitude_dbfs - rms_dbfs

        # 3. Clipping Detection
        clipped_mask = np.abs(audio) >= 0.999
        clipped_sample_count = int(np.sum(clipped_mask))
        clipped_sample_percentage = float((clipped_sample_count / (samples * channels)) * 100.0)
        has_clipping = clipped_sample_count > 0

        # 4. Integrated Loudness (LUFS) using pyloudnorm (BS.1770)
        integrated_lufs = cls._calculate_lufs(audio, sample_rate)

        # 5. Silence & Noise Floor Analysis
        silence_regions, silence_pct, est_snr_db, noise_confidence = cls._analyze_silence_and_noise(
            audio_2d, sample_rate, duration_seconds
        )

        # 6. Frequency Distribution & Spectral Characteristics
        freq_bands = cls._analyze_frequency_bands(audio_2d, sample_rate)

        # 7. Problem Identification & Diagnosis
        quality_problems, recommendations = cls._diagnose_problems(
            duration_seconds=duration_seconds,
            peak_dbfs=peak_amplitude_dbfs,
            rms_dbfs=rms_dbfs,
            crest_factor_db=crest_factor_db,
            integrated_lufs=integrated_lufs,
            true_peak_dbtp=true_peak_dbtp,
            has_clipping=has_clipping,
            clipped_sample_count=clipped_sample_count,
            clipped_sample_percentage=clipped_sample_percentage,
            est_snr_db=est_snr_db,
            freq_bands=freq_bands,
            channels=channels
        )

        # 8. Reciter Vocal Profile & Character Analysis
        vocal_profile = cls._analyze_reciter_vocal_profile(
            audio_2d, sample_rate, freq_bands, est_snr_db, rms_dbfs
        )

        return {
            "duration_seconds": round(duration_seconds, 3),
            "sample_rate": sample_rate,
            "channels": channels,
            "peak_amplitude_dbfs": round(peak_amplitude_dbfs, 2),
            "rms_dbfs": round(rms_dbfs, 2),
            "crest_factor_db": round(crest_factor_db, 2),
            "integrated_lufs": round(integrated_lufs, 2) if integrated_lufs is not None else None,
            "true_peak_dbtp": round(true_peak_dbtp, 2) if true_peak_dbtp is not None else None,
            "silence_regions": silence_regions,
            "silence_percentage": round(silence_pct, 2),
            "estimated_snr_db": round(est_snr_db, 2) if est_snr_db is not None else None,
            "noise_estimation_confidence": noise_confidence,
            "frequency_bands": freq_bands,
            "quality_problems": quality_problems,
            "vocal_profile": vocal_profile,
            "recommendations": recommendations,
        }

    @staticmethod
    def _empty_report(sample_rate: int, channels: int) -> Dict[str, Any]:
        return {
            "duration_seconds": 0.0,
            "sample_rate": sample_rate,
            "channels": channels,
            "peak_amplitude_dbfs": -96.0,
            "rms_dbfs": -96.0,
            "crest_factor_db": 0.0,
            "integrated_lufs": -96.0,
            "true_peak_dbtp": -96.0,
            "silence_regions": [],
            "silence_percentage": 100.0,
            "estimated_snr_db": 0.0,
            "noise_estimation_confidence": "measured",
            "frequency_bands": {
                "sub_bass_energy_db": -96.0,
                "bass_energy_db": -96.0,
                "low_mid_energy_db": -96.0,
                "mid_energy_db": -96.0,
                "high_mid_energy_db": -96.0,
                "presence_high_energy_db": -96.0,
                "air_energy_db": -96.0,
                "spectral_centroid_hz": 0.0,
                "spectral_rolloff_hz": 0.0
            },
            "quality_problems": {
                "has_clipping": False,
                "clipped_sample_count": 0,
                "clipped_sample_percentage": 0.0,
                "has_sub_rumble": False,
                "has_boxiness_mud": False,
                "has_excessive_sibilance": False,
                "has_high_noise_floor": False,
                "is_too_quiet": True,
                "has_excessive_dynamic_range": False,
                "is_mono": channels == 1
            },
            "recommendations": ["Audio file is silent or empty."]
        }

    @classmethod
    def _calculate_true_peak(cls, audio: np.ndarray, sample_rate: int) -> float:
        """
        ITU-R BS.1770-4 4x oversampling True Peak meter.
        """
        try:
            # Resample mono or each channel by 4x
            mono = audio if audio.ndim == 1 else np.mean(audio, axis=1)
            # Use polyphase filtering for fast accurate 4x upsampling
            # Limit computation length if audio is very long for efficiency
            chunk_size = min(len(mono), sample_rate * 300) # up to 5 min
            target_signal = mono[:chunk_size]
            upsampled = scipy.signal.resample_poly(target_signal, 4, 1)
            true_peak_val = float(np.max(np.abs(upsampled)))
            return 20.0 * math.log10(max(true_peak_val, 1e-9))
        except Exception:
            # Fallback to sample peak
            max_val = float(np.max(np.abs(audio)))
            return 20.0 * math.log10(max(max_val, 1e-9))

    @classmethod
    def _calculate_lufs(cls, audio: np.ndarray, sample_rate: int) -> Optional[float]:
        try:
            # pyloudnorm requires audio in shape (samples, channels) or (samples,)
            # If duration < 0.4s, BS.1770 cannot form a gating block
            duration = len(audio) / sample_rate
            if duration < 0.4:
                # Approximate with RMS - 3dB
                rms_val = float(np.sqrt(np.mean(np.square(audio))))
                return 20.0 * math.log10(max(rms_val, 1e-9)) - 3.0
            
            meter = pyln.Meter(sample_rate)
            lufs = float(meter.integrated_loudness(audio))
            if math.isnan(lufs) or math.isinf(lufs):
                return -70.0
            return max(-70.0, lufs)
        except Exception:
            rms_val = float(np.sqrt(np.mean(np.square(audio))))
            return 20.0 * math.log10(max(rms_val, 1e-9)) - 3.0

    @classmethod
    def _analyze_silence_and_noise(
        cls, audio_2d: np.ndarray, sample_rate: int, duration_seconds: float
    ) -> Tuple[List[Dict[str, float]], float, Optional[float], str]:
        """
        Splits audio into 50ms frames to detect silence regions and extract noise profile.
        Distinguishes between verified measured noise vs estimated noise floor.
        """
        mono = np.mean(audio_2d, axis=1)
        frame_len = int(sample_rate * 0.05)  # 50ms
        if frame_len <= 0 or len(mono) < frame_len:
            return [], 0.0, None, "estimated"

        num_frames = len(mono) // frame_len
        frames = mono[:num_frames * frame_len].reshape(num_frames, frame_len)
        frame_rms = np.sqrt(np.mean(np.square(frames), axis=1))
        frame_db = 20.0 * np.log10(np.maximum(frame_rms, 1e-9))

        silence_threshold_db = -50.0
        silence_mask = frame_db < silence_threshold_db

        # Find continuous silence segments >= 250ms (5 consecutive frames)
        silence_regions: List[Dict[str, float]] = []
        consecutive = 0
        start_frame = 0
        min_consecutive_frames = 5

        for i, is_silent in enumerate(silence_mask):
            if is_silent:
                if consecutive == 0:
                    start_frame = i
                consecutive += 1
            else:
                if consecutive >= min_consecutive_frames:
                    silence_regions.append({
                        "start_seconds": round(start_frame * 0.05, 3),
                        "end_seconds": round((start_frame + consecutive) * 0.05, 3),
                        "duration_seconds": round(consecutive * 0.05, 3)
                    })
                consecutive = 0
        if consecutive >= min_consecutive_frames:
            silence_regions.append({
                "start_seconds": round(start_frame * 0.05, 3),
                "end_seconds": round((start_frame + consecutive) * 0.05, 3),
                "duration_seconds": round(consecutive * 0.05, 3)
            })

        total_silence_duration = sum(r["duration_seconds"] for r in silence_regions)
        silence_percentage = (total_silence_duration / duration_seconds) * 100.0 if duration_seconds > 0 else 0.0

        # Noise estimation
        # If quiet segments of at least 300ms exist:
        if len(silence_regions) > 0 and any(r["duration_seconds"] >= 0.3 for r in silence_regions):
            # True quiet pauses exist: measure actual pause noise floor
            pause_frames = [
                frame_db[int(r["start_seconds"] / 0.05):int(r["end_seconds"] / 0.05)]
                for r in silence_regions if r["duration_seconds"] >= 0.3
            ]
            noise_floor_db = float(np.median(np.concatenate(pause_frames)))
            confidence = "measured"
        else:
            # Continuous singing/recitation: estimate from the 5th percentile lowest frames
            noise_floor_db = float(np.percentile(frame_db, 5))
            confidence = "estimated"

        # Signal level from top 20% active frames
        active_frames = frame_db[frame_db > -45.0]
        if len(active_frames) > 0:
            signal_db = float(np.percentile(active_frames, 80))
            est_snr_db = max(0.0, signal_db - noise_floor_db)
        else:
            est_snr_db = 10.0

        return silence_regions[:10], silence_percentage, est_snr_db, confidence

    @classmethod
    def _analyze_frequency_bands(cls, audio_2d: np.ndarray, sample_rate: int) -> Dict[str, float]:
        mono = np.mean(audio_2d, axis=1)
        # Compute Power Spectral Density using Welch's method
        nperseg = min(len(mono), 4096)
        if nperseg < 256:
            return {
                "sub_bass_energy_db": -60.0,
                "bass_energy_db": -50.0,
                "low_mid_energy_db": -40.0,
                "mid_energy_db": -35.0,
                "high_mid_energy_db": -40.0,
                "presence_high_energy_db": -45.0,
                "air_energy_db": -55.0,
                "spectral_centroid_hz": 1500.0,
                "spectral_rolloff_hz": 4000.0
            }

        freqs, psd = scipy.signal.welch(mono, fs=sample_rate, nperseg=nperseg)
        psd_total = np.sum(psd) + 1e-12

        def band_energy(f_low: float, f_high: float) -> float:
            idx = (freqs >= f_low) & (freqs < f_high)
            if not np.any(idx):
                return -96.0
            band_sum = np.sum(psd[idx])
            # Return relative dB normalized to total spectral power
            ratio = max(band_sum / psd_total, 1e-6)
            return round(10.0 * math.log10(ratio), 2)

        # Spectral Centroid (Center of mass)
        centroid = float(np.sum(freqs * psd) / psd_total)

        # Spectral Rolloff (85% energy frequency)
        cum_energy = np.cumsum(psd)
        rolloff_idx = np.searchsorted(cum_energy, 0.85 * psd_total)
        rolloff = float(freqs[min(rolloff_idx, len(freqs) - 1)])

        return {
            "sub_bass_energy_db": band_energy(0.0, 60.0),
            "bass_energy_db": band_energy(60.0, 250.0),
            "low_mid_energy_db": band_energy(250.0, 500.0),
            "mid_energy_db": band_energy(500.0, 2000.0),
            "high_mid_energy_db": band_energy(2000.0, 5000.0),
            "presence_high_energy_db": band_energy(5000.0, 10000.0),
            "air_energy_db": band_energy(10000.0, sample_rate / 2.0),
            "spectral_centroid_hz": round(centroid, 1),
            "spectral_rolloff_hz": round(rolloff, 1),
        }

    @classmethod
    def _diagnose_problems(
        cls,
        duration_seconds: float,
        peak_dbfs: float,
        rms_dbfs: float,
        crest_factor_db: float,
        integrated_lufs: Optional[float],
        true_peak_dbtp: Optional[float],
        has_clipping: bool,
        clipped_sample_count: int,
        clipped_sample_percentage: float,
        est_snr_db: Optional[float],
        freq_bands: Dict[str, float],
        channels: int
    ) -> Tuple[Dict[str, Any], List[str]]:
        
        has_sub_rumble = freq_bands["sub_bass_energy_db"] > -18.0
        # Mud if low-mids (250-500) significantly outweigh high-mids (2k-5k)
        has_boxiness_mud = (freq_bands["low_mid_energy_db"] - freq_bands["high_mid_energy_db"]) > 5.0
        # Sibilance if 5k-10k energy is abnormally high compared to mids
        has_excessive_sibilance = (freq_bands["presence_high_energy_db"] - freq_bands["mid_energy_db"]) > -2.0
        has_high_noise_floor = est_snr_db is not None and est_snr_db < 22.0
        is_too_quiet = (integrated_lufs is not None and integrated_lufs < -23.0) or rms_dbfs < -26.0
        has_excessive_dynamic_range = crest_factor_db > 16.0
        is_mono = channels == 1

        recommendations = []
        if has_clipping:
            recommendations.append(
                f"Severe digital clipping detected ({clipped_sample_count} samples). Lookahead peak limiter will prevent post-processing distortion."
            )
        if has_sub_rumble:
            recommendations.append(
                "Excessive low-frequency rumble below 60 Hz detected. Apply high-pass filtering (75 Hz cutoff) to clean up microphone handling noise."
            )
        if has_boxiness_mud:
            recommendations.append(
                "Boxy room resonance or mud in the 250-500 Hz region. Gentle parametric cut recommended to clarify vocal fundamentals."
            )
        if has_excessive_sibilance:
            recommendations.append(
                "Harsh sibilance detected in the 5-8 kHz range. De-essing recommended to soften sharp Arabic/Urdu consonants ('seen', 'sheen', 'tay')."
            )
        if has_high_noise_floor:
            recommendations.append(
                f"Elevated background hiss or environmental noise (estimated SNR ~{est_snr_db:.1f} dB). Moderate spectral noise suppression recommended."
            )
        if is_too_quiet:
            recommendations.append(
                f"Vocal level is quiet ({integrated_lufs or rms_dbfs:.1f} LUFS/dBFS). Target standard vocal delivery (-16 LUFS) with transparent dynamics control."
            )
        if has_excessive_dynamic_range:
            recommendations.append(
                "Dynamic range is uneven across recitation sections. Controlled vocal compression recommended for consistent intimacy."
            )
        if not recommendations:
            recommendations.append("Audio is well-balanced. Gentle enhancement with transparent air and subtle warmth is recommended.")

        problems = {
            "has_clipping": has_clipping,
            "clipped_sample_count": clipped_sample_count,
            "clipped_sample_percentage": round(clipped_sample_percentage, 4),
            "has_sub_rumble": has_sub_rumble,
            "has_boxiness_mud": has_boxiness_mud,
            "has_excessive_sibilance": has_excessive_sibilance,
            "has_high_noise_floor": has_high_noise_floor,
            "is_too_quiet": is_too_quiet,
            "has_excessive_dynamic_range": has_excessive_dynamic_range,
            "is_mono": is_mono
        }

        return problems, recommendations

    @classmethod
    def _analyze_reciter_vocal_profile(
        cls,
        audio_2d: np.ndarray,
        sample_rate: int,
        freq_bands: Dict[str, float],
        est_snr_db: Optional[float],
        rms_dbfs: float
    ) -> Dict[str, Any]:
        """
        AI Vocal Profiler for Naat reciters:
        Measures fundamental frequency range (F0), voice register (Baritone, Tenor, Alto),
        vocal warmth vs brightness, and recommends the best personalized reciter preset.
        """
        mono = np.mean(audio_2d, axis=1)
        # Fast autocorrelation pitch estimation on 100ms mid-energy chunks
        frame_len = int(sample_rate * 0.1)
        hop = frame_len
        n_frames = min(20, (len(mono) - frame_len) // hop)
        
        detected_pitches = []
        for i in range(max(1, n_frames)):
            f_slice = mono[i * hop : i * hop + frame_len]
            if np.sqrt(np.mean(f_slice ** 2)) > 0.01:
                # Autocorrelation
                corr = np.correlate(f_slice, f_slice, mode="full")
                corr = corr[len(corr) // 2 :]
                d = np.diff(corr)
                starts = np.where(d > 0)[0]
                if len(starts) > 0:
                    peak_idx = starts[0] + np.argmax(corr[starts[0] :])
                    if peak_idx > 0:
                        pitch = float(sample_rate / peak_idx)
                        if 75.0 <= pitch <= 550.0:
                            detected_pitches.append(pitch)

        median_f0 = float(np.median(detected_pitches)) if detected_pitches else 170.0

        if median_f0 < 135.0:
            vocal_register = "Baritone / Low Chest"
            recommended_preset = "deep_baritone"
            preset_reason = "Deep baritone vocal register detected. Deep Baritone preset with 300Hz mud clearing and rich tube warmth recommended."
        elif median_f0 > 230.0:
            vocal_register = "Alto / Youthful High"
            recommended_preset = "youth_vocal"
            preset_reason = "High-pitched vocal register detected. Youth Vocal preset with 4.2kHz de-harshing and fast pitch stabilization recommended."
        else:
            vocal_register = "Tenor / Mid Vocal"
            if est_snr_db is not None and est_snr_db < 20.0:
                recommended_preset = "jalsa_live"
                preset_reason = "Live recording with prominent background noise. Jalsa Live Master with heavy downward gating and peak leveling recommended."
            elif (freq_bands.get("air_energy_db", -50) > -35.0):
                recommended_preset = "modern_nasheed"
                preset_reason = "Clean vocal with open high-frequency air. Modern Nasheed Studio preset with stereo vocal doubler and analog echo recommended."
            else:
                recommended_preset = "studio_naat"
                preset_reason = "Balanced vocal delivery. Studio Master preset with pitch snapping, warm tube saturation, and -14 LUFS mastering recommended."

        # Vocal Timbre Character
        low_energy = freq_bands.get("bass_energy_db", -20) + freq_bands.get("low_mid_energy_db", -20)
        high_energy = freq_bands.get("high_mid_energy_db", -20) + freq_bands.get("presence_high_energy_db", -20)
        if (high_energy - low_energy) > 4.0:
            timbre = "Bright & Articulate"
        elif (low_energy - high_energy) > 6.0:
            timbre = "Warm & Resonant"
        else:
            timbre = "Balanced Acoustic"

        return {
            "estimated_f0_hz": round(median_f0, 1),
            "vocal_register": vocal_register,
            "vocal_timbre": timbre,
            "recommended_preset": recommended_preset,
            "personalized_reason": preset_reason
        }
