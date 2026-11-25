import os
import re
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import soundfile as sf
import numpy as np

from app.core.config import settings
from app.database.session import get_db
from app.models.audio_file import AudioFile
from app.schemas.audio import AudioUploadResponse, AudioFileMetadata, AudioAnalysisReport, AudioEditRequest
from app.audio_engine.analyzer import AudioAnalyzer

router = APIRouter(prefix="/audio", tags=["Audio"])

def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    return cleaned[:100]

@router.post("/upload", response_model=AudioUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_audio(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Supported formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    contents = file.file.read()
    file_size = len(contents)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum upload limit of {settings.MAX_UPLOAD_SIZE_MB} MB."
        )

    audio_id = str(uuid.uuid4())
    sanitized_name = sanitize_filename(file.filename)
    stored_name = f"{audio_id}_{sanitized_name}"
    rel_path = f"storage/originals/{stored_name}"
    abs_path = os.path.join(settings.BASE_DIR, rel_path)

    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(contents)

    # Validate actual decoded audio
    try:
        audio_data, sample_rate = sf.read(abs_path, dtype="float32", always_2d=False)
    except Exception as e:
        # If soundfile fails directly (e.g. webm or ogg from browser MediaRecorder), transcode cleanly via FFmpeg
        temp_wav = abs_path + ".converted.wav"
        try:
            import subprocess
            cmd = ["ffmpeg", "-y", "-i", abs_path, "-ar", "44100", temp_wav]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res.returncode == 0 and os.path.exists(temp_wav):
                import shutil
                shutil.move(temp_wav, abs_path)
                audio_data, sample_rate = sf.read(abs_path, dtype="float32", always_2d=False)
            else:
                if os.path.exists(abs_path):
                    os.remove(abs_path)
                raise HTTPException(
                    status_code=400,
                    detail=f"Uploaded audio could not be decoded: {str(e)}"
                )
        except Exception as ex:
            if os.path.exists(abs_path):
                os.remove(abs_path)
            raise HTTPException(
                status_code=400,
                detail=f"Uploaded file is corrupt or unsupported: {str(ex)}"
            )

    channels = 1 if audio_data.ndim == 1 else audio_data.shape[1]
    duration = float(len(audio_data) / sample_rate) if sample_rate > 0 else 0.0

    if duration < 0.2:
        if os.path.exists(abs_path):
            os.remove(abs_path)
        raise HTTPException(
            status_code=400,
            detail="Audio recording is too short (minimum 0.2 seconds required)."
        )

    if duration > settings.MAX_AUDIO_DURATION_SECONDS:
        if os.path.exists(abs_path):
            os.remove(abs_path)
        max_mins = settings.MAX_AUDIO_DURATION_SECONDS // 60
        raise HTTPException(
            status_code=400,
            detail=f"Audio recording exceeds maximum allowed duration of {max_mins} minutes ({settings.MAX_AUDIO_DURATION_SECONDS}s)."
        )

    analysis_report = AudioAnalyzer.analyze(audio_data, sample_rate)

    audio_file_record = AudioFile(
        id=audio_id,
        original_filename=file.filename,
        sanitized_filename=sanitized_name,
        file_format=ext.replace(".", ""),
        duration_seconds=round(duration, 3),
        sample_rate=sample_rate,
        channels=channels,
        file_size_bytes=file_size,
        storage_relative_path=rel_path,
        analysis_data=analysis_report
    )
    db.add(audio_file_record)
    db.commit()
    db.refresh(audio_file_record)

    return AudioUploadResponse(
        audio_id=audio_id,
        filename=file.filename,
        duration_seconds=round(duration, 3),
        sample_rate=sample_rate,
        channels=channels,
        file_size_bytes=file_size,
        analysis=analysis_report,
        message="Audio uploaded and analyzed successfully"
    )

SAMPLE_LIBRARY = {
    "hijaz": {
        "file": "naat_sample_1_hijaz.wav",
        "title": "Faslon Ko Takalluf (Maqam Hijaz)",
        "description": "Urdu spiritual Naat vocal with characteristic Eastern minor 2nd intervals, natural breathing, subtle room boxiness and background hiss."
    },
    "burda": {
        "file": "naat_sample_2_burda.wav",
        "title": "Qasida Burda Sharif (Arabic Recitation)",
        "description": "Classical Arabic spiritual ode with dynamic melodic phrasing, vocal resonance, and room acoustics."
    },
    "salam": {
        "file": "naat_sample_3_salam.wav",
        "title": "Mustafa Jane Rehmat (Warm Salam)",
        "description": "Traditional soulful salam cadence in baritone register with chest resonance and mic proximity effect."
    }
}

@router.get("/samples/list")
def list_available_samples():
    """Returns curated library of pre-recorded authentic Naat vocal samples."""
    return [
        {
            "id": k,
            "title": v["title"],
            "description": v["description"]
        }
        for k, v in SAMPLE_LIBRARY.items()
    ]

@router.post("/load-sample/{sample_key}", response_model=AudioUploadResponse)
def load_specific_sample_audio(sample_key: str, db: Session = Depends(get_db)):
    """Loads a specific pre-packaged demo Naat vocal from the curated library."""
    if sample_key not in SAMPLE_LIBRARY:
        # Default to hijaz if unknown key
        sample_key = "hijaz"

    sample_meta = SAMPLE_LIBRARY[sample_key]
    sample_src = os.path.join(settings.SAMPLES_DIR, sample_meta["file"])
    if not os.path.exists(sample_src):
        sample_src = os.path.join(settings.STORAGE_DIR, "samples", sample_meta["file"])
    if not os.path.exists(sample_src):
        sample_src = os.path.join(settings.SAMPLES_DIR, "sample_naat_with_noise.wav")
    if not os.path.exists(sample_src):
        sample_src = os.path.join(settings.STORAGE_DIR, "samples", "sample_naat_with_noise.wav")

    audio_id = str(uuid.uuid4())
    stored_name = f"{audio_id}_{sample_meta['file']}"
    rel_path = f"storage/originals/{stored_name}"
    abs_path = os.path.join(settings.BASE_DIR, rel_path)

    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    import shutil
    shutil.copyfile(sample_src, abs_path)

    audio_data, sample_rate = sf.read(abs_path, dtype="float32", always_2d=False)
    channels = 1 if audio_data.ndim == 1 else audio_data.shape[1]
    duration = float(len(audio_data) / sample_rate)

    analysis_report = AudioAnalyzer.analyze(audio_data, sample_rate)

    audio_file_record = AudioFile(
        id=audio_id,
        original_filename=sample_meta["title"] + ".wav",
        sanitized_filename=sample_meta["file"],
        file_format="wav",
        duration_seconds=round(duration, 3),
        sample_rate=sample_rate,
        channels=channels,
        file_size_bytes=os.path.getsize(abs_path),
        storage_relative_path=rel_path,
        analysis_data=analysis_report
    )
    db.add(audio_file_record)
    db.commit()
    db.refresh(audio_file_record)

    return AudioUploadResponse(
        audio_id=audio_id,
        filename=sample_meta["title"] + ".wav",
        duration_seconds=round(duration, 3),
        sample_rate=sample_rate,
        channels=channels,
        file_size_bytes=audio_file_record.file_size_bytes,
        analysis=analysis_report,
        message=f"Sample '{sample_meta['title']}' loaded and analyzed successfully"
    )

@router.post("/load-sample", response_model=AudioUploadResponse)
def load_sample_audio(db: Session = Depends(get_db)):
    """Loads default demo Naat vocal."""
    return load_specific_sample_audio("hijaz", db)

@router.get("/{audio_id}", response_model=AudioFileMetadata)
def get_audio_info(audio_id: str, db: Session = Depends(get_db)):
    audio = db.query(AudioFile).filter(AudioFile.id == audio_id).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Audio file not found")
    return audio.to_dict()

@router.get("/{audio_id}/metadata", response_model=AudioFileMetadata)
def get_audio_metadata(audio_id: str, db: Session = Depends(get_db)):
    audio = db.query(AudioFile).filter(AudioFile.id == audio_id).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Audio file not found")
    return audio.to_dict()

@router.get("/{audio_id}/analysis", response_model=AudioAnalysisReport)
def get_audio_analysis(audio_id: str, db: Session = Depends(get_db)):
    audio = db.query(AudioFile).filter(AudioFile.id == audio_id).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Audio file not found")
    if not audio.analysis_data:
        raise HTTPException(status_code=404, detail="Analysis data not available")
    return audio.analysis_data

@router.get("/{audio_id}/stream")
def stream_audio_file(audio_id: str, db: Session = Depends(get_db)):
    audio = db.query(AudioFile).filter(AudioFile.id == audio_id).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Audio file not found")
    abs_path = os.path.join(settings.BASE_DIR, audio.storage_relative_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="Audio file missing on disk")
    media_type = f"audio/{audio.file_format}" if audio.file_format != "mp3" else "audio/mpeg"
    return FileResponse(abs_path, media_type=media_type, filename=audio.sanitized_filename)

@router.post("/{audio_id}/edit", response_model=AudioUploadResponse)
def edit_audio_file(
    audio_id: str,
    payload: AudioEditRequest,
    db: Session = Depends(get_db)
):
    audio_record = db.query(AudioFile).filter(AudioFile.id == audio_id).first()
    if not audio_record:
        raise HTTPException(status_code=404, detail="Audio file not found")

    abs_path = os.path.join(settings.BASE_DIR, audio_record.storage_relative_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="Original audio file missing on disk")

    audio_data, sample_rate = sf.read(abs_path, dtype="float32", always_2d=False)
    total_samples = len(audio_data)

    start_sample = int((payload.start_seconds or 0.0) * sample_rate)
    end_sample = int(payload.end_seconds * sample_rate) if payload.end_seconds is not None else total_samples

    start_sample = max(0, min(start_sample, total_samples - int(sample_rate * 0.2)))
    end_sample = max(start_sample + int(sample_rate * 0.2), min(end_sample, total_samples))

    edited = audio_data[start_sample:end_sample].copy()

    # Pre-gain trim if requested
    if payload.gain_db and abs(payload.gain_db) > 0.01:
        linear_gain = 10.0 ** (payload.gain_db / 20.0)
        edited *= linear_gain

    # Apply smooth 15ms anti-click crossfade
    fade_samples = min(int(sample_rate * 0.015), len(edited) // 4)
    if fade_samples > 0:
        fade_in = np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)
        fade_out = np.linspace(1.0, 0.0, fade_samples, dtype=np.float32)
        if edited.ndim == 1:
            edited[:fade_samples] *= fade_in
            edited[-fade_samples:] *= fade_out
        else:
            edited[:fade_samples] *= fade_in[:, np.newaxis]
            edited[-fade_samples:] *= fade_out[:, np.newaxis]

    # Save as new AudioFile
    new_id = str(uuid.uuid4())
    clean_name = f"edited_{audio_record.sanitized_filename}"
    stored_name = f"{new_id}_{clean_name}"
    rel_path = f"storage/originals/{stored_name}"
    new_abs_path = os.path.join(settings.BASE_DIR, rel_path)

    os.makedirs(os.path.dirname(new_abs_path), exist_ok=True)
    sf.write(new_abs_path, edited, sample_rate, subtype="PCM_24", format="WAV")

    channels = 1 if edited.ndim == 1 else edited.shape[1]
    duration = float(len(edited) / sample_rate)
    analysis_report = AudioAnalyzer.analyze(edited, sample_rate)

    new_record = AudioFile(
        id=new_id,
        original_filename=f"Edited - {audio_record.original_filename}",
        sanitized_filename=clean_name,
        file_format="wav",
        duration_seconds=round(duration, 3),
        sample_rate=sample_rate,
        channels=channels,
        file_size_bytes=os.path.getsize(new_abs_path),
        storage_relative_path=rel_path,
        analysis_data=analysis_report
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return AudioUploadResponse(
        audio_id=new_id,
        filename=new_record.original_filename,
        duration_seconds=round(duration, 3),
        sample_rate=sample_rate,
        channels=channels,
        file_size_bytes=new_record.file_size_bytes,
        analysis=analysis_report,
        message="Audio edited and trimmed successfully"
    )

@router.delete("/{audio_id}", status_code=status.HTTP_200_OK)
def delete_audio(audio_id: str, db: Session = Depends(get_db)):
    audio = db.query(AudioFile).filter(AudioFile.id == audio_id).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Audio file not found")

    abs_path = os.path.join(settings.BASE_DIR, audio.storage_relative_path)
    if os.path.exists(abs_path):
        try:
            os.remove(abs_path)
        except OSError:
            pass

    db.delete(audio)
    db.commit()
    return {"message": "Audio file deleted successfully", "id": audio_id}
