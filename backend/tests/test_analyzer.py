import pytest
import numpy as np
from app.audio_engine.analyzer import AudioAnalyzer

def test_clean_vocal_analysis(synthetic_audio_factory):
    sr = 44100
    signal = synthetic_audio_factory("clean_vocal", duration=2.5, sample_rate=sr)
    report = AudioAnalyzer.analyze(signal, sr)

    assert report["duration_seconds"] == 2.5
    assert report["sample_rate"] == 44100
    assert report["channels"] == 1
    assert report["peak_amplitude_dbfs"] < 0.0
    assert report["peak_amplitude_dbfs"] > -12.0
    assert report["rms_dbfs"] < report["peak_amplitude_dbfs"]
    assert report["crest_factor_db"] > 3.0
    assert report["integrated_lufs"] is not None
    assert report["quality_problems"]["has_clipping"] is False
    assert len(report["recommendations"]) > 0

def test_noisy_signal_analysis(synthetic_audio_factory):
    sr = 44100
    signal = synthetic_audio_factory("noisy", duration=2.0, sample_rate=sr)
    report = AudioAnalyzer.analyze(signal, sr)

    assert report["estimated_snr_db"] is not None
    assert report["estimated_snr_db"] < 25.0
    assert report["quality_problems"]["has_high_noise_floor"] is True

def test_clipped_signal_analysis(synthetic_audio_factory):
    sr = 44100
    signal = synthetic_audio_factory("clipped", duration=1.5, sample_rate=sr)
    report = AudioAnalyzer.analyze(signal, sr)

    assert report["quality_problems"]["has_clipping"] is True
    assert report["quality_problems"]["clipped_sample_count"] > 100
    assert any("clipping" in r.lower() for r in report["recommendations"])

def test_quiet_signal_analysis(synthetic_audio_factory):
    sr = 44100
    signal = synthetic_audio_factory("quiet", duration=1.0, sample_rate=sr)
    report = AudioAnalyzer.analyze(signal, sr)

    assert report["quality_problems"]["is_too_quiet"] is True

def test_silent_signal_analysis(synthetic_audio_factory):
    sr = 44100
    signal = synthetic_audio_factory("silent", duration=1.0, sample_rate=sr)
    report = AudioAnalyzer.analyze(signal, sr)

    assert report["duration_seconds"] == 1.0
    assert report["peak_amplitude_dbfs"] <= -90.0

def test_sub_rumble_signal_analysis(synthetic_audio_factory):
    sr = 44100
    signal = synthetic_audio_factory("rumble", duration=2.0, sample_rate=sr)
    report = AudioAnalyzer.analyze(signal, sr)

    assert report["quality_problems"]["has_sub_rumble"] is True
    assert any("rumble" in r.lower() or "high-pass" in r.lower() for r in report["recommendations"])

def test_stereo_signal_analysis(synthetic_audio_factory):
    sr = 48000
    signal = synthetic_audio_factory("clean_vocal", duration=1.5, sample_rate=sr, stereo=True)
    report = AudioAnalyzer.analyze(signal, sr)

    assert report["channels"] == 2
    assert report["sample_rate"] == 48000
    assert report["quality_problems"]["is_mono"] is False
