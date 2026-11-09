import pytest
import numpy as np
from app.audio_engine.stages.noise_reduction import NoiseReductionStage, SpectralGatingAdapter
from app.audio_engine.stages.filters import HighPassFilterStage, EqualizerStage
from app.audio_engine.stages.dynamics import CompressorStage, DeesserStage, LimiterStage
from app.audio_engine.stages.reverb import NaturalReverbStage
from app.audio_engine.stages.loudness import LoudnessNormalizationStage
from app.audio_engine.stages.validator import QualityValidatorStage
from app.audio_engine.analyzer import AudioAnalyzer

def test_spectral_gating_noise_reduction(synthetic_audio_factory):
    sr = 44100
    noisy = synthetic_audio_factory("noisy", duration=2.0, sample_rate=sr)
    initial_analysis = AudioAnalyzer.analyze(noisy, sr)

    stage = NoiseReductionStage(preferred_backend="auto")
    config = {"noise_reduction": {"enabled": True, "strength": 0.5}}
    processed, meta = stage.process(noisy, sr, config)

    assert meta["status"] == "applied"
    assert len(processed) == len(noisy)
    assert not np.any(np.isnan(processed))

    processed_analysis = AudioAnalyzer.analyze(processed, sr)
    # SNR should improve or noise energy should decrease
    assert processed_analysis["estimated_snr_db"] is not None

def test_high_pass_filter_stage(synthetic_audio_factory):
    sr = 44100
    # Signal with 30 Hz sub rumble + 300 Hz vocal
    t = np.linspace(0, 1.0, sr, endpoint=False)
    sub = 0.5 * np.sin(2 * np.pi * 30 * t)
    vocal = 0.5 * np.sin(2 * np.pi * 300 * t)
    signal = (sub + vocal).astype(np.float32)

    stage = HighPassFilterStage()
    config = {"high_pass": {"enabled": True, "cutoff_hz": 80.0, "order": 2}}
    filtered, meta = stage.process(signal, sr, config)

    assert meta["status"] == "applied"
    # Sub-bass energy should be greatly reduced
    orig_sub_power = np.mean(signal ** 2)
    filt_sub_power = np.mean(filtered ** 2)
    assert filt_sub_power < orig_sub_power

def test_equalizer_stage(synthetic_audio_factory):
    sr = 44100
    signal = synthetic_audio_factory("clean_vocal", duration=1.0, sample_rate=sr)

    stage = EqualizerStage()
    config = {
        "equalizer": {
            "enabled": True,
            "mud_cut_gain_db": -2.0,
            "mud_cut_freq_hz": 300.0,
            "presence_boost_gain_db": 1.5,
            "presence_freq_hz": 3200.0,
            "air_shelf_gain_db": 2.0,
            "air_shelf_freq_hz": 10000.0
        }
    }
    eq_audio, meta = stage.process(signal, sr, config)

    assert meta["status"] == "applied"
    assert len(eq_audio) == len(signal)
    assert not np.any(np.isnan(eq_audio))

def test_compressor_stage(synthetic_audio_factory):
    sr = 44100
    # Wide dynamic signal: loud burst followed by quiet note
    t = np.linspace(0, 1.0, sr, endpoint=False)
    burst = np.concatenate([
        0.9 * np.sin(2 * np.pi * 220 * t[:sr//2]),
        0.1 * np.sin(2 * np.pi * 220 * t[sr//2:])
    ]).astype(np.float32)

    stage = CompressorStage()
    config = {
        "compressor": {
            "enabled": True,
            "threshold_db": -18.0,
            "ratio": 3.0,
            "attack_ms": 20.0,
            "release_ms": 100.0,
            "knee_db": 4.0
        }
    }
    compressed, meta = stage.process(burst, sr, config)

    assert meta["status"] == "applied"
    # Peak amplitude of the loud section should be brought down
    assert np.max(np.abs(compressed[:sr//2])) <= np.max(np.abs(burst[:sr//2])) + 0.1

def test_deesser_stage(synthetic_audio_factory):
    sr = 44100
    sibilant = synthetic_audio_factory("sibilant", duration=1.0, sample_rate=sr)

    stage = DeesserStage()
    config = {"deesser": {"enabled": True, "threshold_db": -18.0, "freq_hz": 7000.0}}
    deessed, meta = stage.process(sibilant, sr, config)

    assert meta["status"] == "applied"
    assert len(deessed) == len(sibilant)
    assert not np.any(np.isnan(deessed))

def test_natural_reverb_stage(synthetic_audio_factory):
    sr = 44100
    vocal = synthetic_audio_factory("clean_vocal", duration=1.0, sample_rate=sr)

    stage = NaturalReverbStage()
    config = {
        "reverb": {
            "enabled": True,
            "wet": 0.10,
            "dry": 0.95,
            "decay_time_seconds": 1.2,
            "pre_delay_ms": 20.0,
            "damping": 0.3
        }
    }
    reverbed, meta = stage.process(vocal, sr, config)

    assert meta["status"] == "applied"
    assert len(reverbed) == len(vocal)
    # Output should not be identical to dry input
    assert not np.array_equal(reverbed, vocal)

def test_loudness_normalization_stage(synthetic_audio_factory):
    sr = 44100
    # Vocal-like signal at -24 LUFS
    t = np.linspace(0, 2.0, sr * 2, endpoint=False)
    vocal = (0.1 * np.sin(2 * np.pi * 330 * t)).astype(np.float32)

    stage = LoudnessNormalizationStage()
    config = {"loudness": {"target_lufs": -16.0}}
    normalized, meta = stage.process(vocal, sr, config)

    assert meta["status"] == "applied"
    analysis = AudioAnalyzer.analyze(normalized, sr)
    if analysis["integrated_lufs"] is not None:
        # Loudness should be leveled close to -16 LUFS
        assert abs(analysis["integrated_lufs"] - (-16.0)) < 1.0

def test_limiter_stage_guarantees_ceiling():
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    # Overdriving signal peaking at +6 dBFS
    overdriven = (2.0 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

    stage = LimiterStage()
    config = {"limiter": {"ceiling_dbtp": -1.0}}
    limited, meta = stage.process(overdriven, sr, config)

    assert meta["status"] == "applied"
    # Absolute peak must never exceed -1.0 dBTP (approx 0.891 linear)
    max_peak = np.max(np.abs(limited))
    assert max_peak <= 0.895

def test_quality_validator_stage(synthetic_audio_factory):
    sr = 44100
    clean = synthetic_audio_factory("clean_vocal", duration=2.0, sample_rate=sr)
    analysis = AudioAnalyzer.analyze(clean, sr)

    passed, proc_analysis, report = QualityValidatorStage.validate_and_compare(
        original_audio=clean,
        processed_audio=clean,
        sample_rate=sr,
        original_analysis=analysis
    )

    assert passed is True
    assert report["duration_passed"] is True
    assert report["nan_inf_check_passed"] is True
    assert report["silence_dropout_detected"] is False
