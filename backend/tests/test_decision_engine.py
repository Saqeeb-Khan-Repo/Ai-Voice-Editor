import pytest
from app.audio_engine.decision_engine import EnhancementDecisionEngine
from app.audio_engine.analyzer import AudioAnalyzer
from app.schemas.processing import ProcessingParametersOverride

def test_natural_naat_preset(synthetic_audio_factory):
    sr = 44100
    signal = synthetic_audio_factory("clean_vocal", duration=2.0, sample_rate=sr)
    analysis = AudioAnalyzer.analyze(signal, sr)

    config, log = EnhancementDecisionEngine.decide(analysis, preset="natural_naat")

    assert config["preset"] == "natural_naat"
    assert config["loudness"]["target_lufs"] == -16.0
    assert config["reverb"]["wet"] <= 0.10
    assert log["preset_selected"] == "natural_naat"
    assert "noise_reduction_decision" in log

def test_studio_naat_preset(synthetic_audio_factory):
    sr = 44100
    signal = synthetic_audio_factory("clean_vocal", duration=2.0, sample_rate=sr)
    analysis = AudioAnalyzer.analyze(signal, sr)

    config, log = EnhancementDecisionEngine.decide(analysis, preset="studio_naat")

    assert config["preset"] == "studio_naat"
    assert config["loudness"]["target_lufs"] == -14.0
    assert config["compressor"]["ratio"] >= 2.0
    assert config["reverb"]["wet"] >= 0.12

def test_spacious_naat_preset(synthetic_audio_factory):
    sr = 44100
    signal = synthetic_audio_factory("clean_vocal", duration=2.0, sample_rate=sr)
    analysis = AudioAnalyzer.analyze(signal, sr)

    config, log = EnhancementDecisionEngine.decide(analysis, preset="spacious_naat")

    assert config["preset"] == "spacious_naat"
    assert config["reverb"]["decay_time_seconds"] >= 2.0
    assert config["reverb"]["wet"] >= 0.20

def test_decision_engine_with_overrides(synthetic_audio_factory):
    sr = 44100
    signal = synthetic_audio_factory("clean_vocal", duration=2.0, sample_rate=sr)
    analysis = AudioAnalyzer.analyze(signal, sr)

    overrides = ProcessingParametersOverride(
        noise_reduction_strength=0.85,
        target_lufs=-14.0,
        output_format="flac"
    )
    config, log = EnhancementDecisionEngine.decide(
        analysis, preset="natural_naat", overrides=overrides
    )

    assert config["noise_reduction"]["strength"] == 0.85
    assert config["loudness"]["target_lufs"] == -14.0
    assert config["output_format"] == "flac"
    assert "User override applied" in log["noise_reduction_decision"]
