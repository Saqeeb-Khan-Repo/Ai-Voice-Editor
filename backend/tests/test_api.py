import io
import time
import pytest
import soundfile as sf
import numpy as np
from fastapi import UploadFile

from app.database.session import SessionLocal
from app.api.health import health_check
from app.api.audio import upload_audio, get_audio_info, get_audio_metadata, get_audio_analysis, delete_audio
from app.api.processing import start_processing_job, get_job_status, list_jobs, cancel_job
from app.api.outputs import get_output_metadata, delete_output_file, download_output_file
from app.api.monitoring import get_overview, get_engine_status, get_storage_usage
from app.api.settings import get_current_settings, update_settings, SettingsUpdateSchema
from app.schemas.processing import ProcessingRequest
from app.models.audio_output import AudioOutput

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_health_check_endpoint():
    res = health_check()
    assert res["status"] == "healthy"
    assert "AI Naat Studio" in res["app"]

def test_audio_upload_and_metadata(db_session, synthetic_audio_factory):
    sr = 44100
    signal = synthetic_audio_factory("clean_vocal", duration=1.0, sample_rate=sr)
    buf = io.BytesIO()
    sf.write(buf, signal, sr, format="WAV")
    buf.seek(0)

    upload_file = UploadFile(filename="test_naat.wav", file=buf)
    res = upload_audio(file=upload_file, db=db_session)

    assert res.audio_id is not None
    assert res.filename == "test_naat.wav"
    assert res.duration_seconds == 1.0
    assert res.analysis is not None
    assert res.analysis.sample_rate == 44100

    # Retrieve info
    info = get_audio_info(res.audio_id, db=db_session)
    assert info["id"] == res.audio_id

    # Retrieve analysis
    ana = get_audio_analysis(res.audio_id, db=db_session)
    assert "frequency_bands" in ana

def test_processing_job_lifecycle(db_session, synthetic_audio_factory):
    sr = 44100
    signal = synthetic_audio_factory("noisy", duration=1.0, sample_rate=sr)
    buf = io.BytesIO()
    sf.write(buf, signal, sr, format="WAV")
    buf.seek(0)

    upload_file = UploadFile(filename="studio_surah.wav", file=buf)
    up = upload_audio(file=upload_file, db=db_session)
    audio_id = up.audio_id

    # Submit processing job
    req = ProcessingRequest(preset="natural_naat", automatic_mode=True)
    job_res = start_processing_job(audio_id=audio_id, req=req, db=db_session)
    assert job_res.job_id is not None
    assert job_res.status in ["pending", "analyzing", "completed"]

    # Poll until background executor completes
    max_wait = 15
    start = time.time()
    final_job = None
    while time.time() - start < max_wait:
        j = get_job_status(job_res.job_id, db=db_session)
        if j.status in ["completed", "failed"]:
            final_job = j
            break
        time.sleep(0.3)

    assert final_job is not None, "Job timed out"
    assert final_job.status == "completed"
    assert final_job.output_id is not None

    # Verify Output metadata
    out_meta = get_output_metadata(final_job.output_id, db=db_session)
    assert out_meta["quality_report"]["overall_quality_passed"] is True
    assert "Leveled integrated loudness" in out_meta["quality_report"]["quality_summary"] or "Cleaned" in out_meta["quality_report"]["quality_summary"] or "Guaranteed" in out_meta["quality_report"]["quality_summary"]

    # Verify Multi-Format Export Downloads (WAV 24-bit, WAV 16-bit, MP3 320 kbps)
    res_wav24 = download_output_file(output_id=final_job.output_id, format="wav_24", db=db_session)
    assert res_wav24.media_type == "audio/wav"
    assert "24bit.wav" in res_wav24.filename

    res_wav16 = download_output_file(output_id=final_job.output_id, format="wav_16", db=db_session)
    assert res_wav16.media_type == "audio/wav"
    assert "16bit.wav" in res_wav16.filename

    res_mp3 = download_output_file(output_id=final_job.output_id, format="mp3_320", db=db_session)
    assert res_mp3.media_type == "audio/mpeg"
    assert "320kbps.mp3" in res_mp3.filename

def test_monitoring_endpoints():
    ov = get_overview()
    assert ov["backend_status"] == "healthy"
    assert ov["engine_status"]["spectral_gating_available"] is True

    eng = get_engine_status()
    assert "AI Naat Studio" in eng["engine_name"]

    st = get_storage_usage()
    assert st["disk_free_bytes"] > 0

def test_settings_endpoints():
    cur = get_current_settings()
    assert "max_upload_size_mb" in cur

    update_payload = SettingsUpdateSchema(max_upload_size_mb=180)
    updated = update_settings(payload=update_payload)
    assert updated["settings"]["max_upload_size_mb"] == 180
