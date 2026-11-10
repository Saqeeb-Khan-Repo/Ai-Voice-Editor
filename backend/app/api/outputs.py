import os
import subprocess
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import soundfile as sf

from app.core.config import settings
from app.database.session import get_db
from app.models.audio_output import AudioOutput
from app.schemas.output import AudioOutputMetadata

router = APIRouter(prefix="/outputs", tags=["Outputs"])

@router.get("/{output_id}/metadata", response_model=AudioOutputMetadata)
def get_output_metadata(output_id: str, db: Session = Depends(get_db)):
    output = db.query(AudioOutput).filter(AudioOutput.id == output_id).first()
    if not output:
        raise HTTPException(status_code=404, detail="Audio output not found")
    return output.to_dict()

@router.get("/{output_id}/download")
def download_output_file(
    output_id: str,
    format: Optional[str] = Query(None, description="Export format: wav_24, wav_16, or mp3_320"),
    db: Session = Depends(get_db)
):
    output = db.query(AudioOutput).filter(AudioOutput.id == output_id).first()
    if not output:
        raise HTTPException(status_code=404, detail="Audio output not found")

    abs_path = os.path.join(settings.BASE_DIR, output.storage_relative_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File missing from storage")

    if not format or format.lower() in ("original", "default"):
        media_type = f"audio/{output.file_format}" if output.file_format != "mp3" else "audio/mpeg"
        return FileResponse(
            abs_path,
            media_type=media_type,
            filename=output.filename,
            headers={"Content-Disposition": f'attachment; filename="{output.filename}"'}
        )

    fmt = format.lower().strip()
    source_stem = Path(abs_path).stem
    processed_dir = Path(abs_path).parent

    if fmt in ("wav_24", "wav-24", "wav"):
        export_filename = f"{source_stem}_24bit.wav"
        target_path = str(processed_dir / export_filename)
        if not os.path.exists(target_path):
            data, sr = sf.read(abs_path, dtype="float32", always_2d=False)
            sf.write(target_path, data, sr, subtype="PCM_24", format="WAV")
        return FileResponse(
            target_path,
            media_type="audio/wav",
            filename=export_filename,
            headers={"Content-Disposition": f'attachment; filename="{export_filename}"'}
        )

    elif fmt in ("wav_16", "wav-16"):
        export_filename = f"{source_stem}_16bit.wav"
        target_path = str(processed_dir / export_filename)
        if not os.path.exists(target_path):
            data, sr = sf.read(abs_path, dtype="float32", always_2d=False)
            sf.write(target_path, data, sr, subtype="PCM_16", format="WAV")
        return FileResponse(
            target_path,
            media_type="audio/wav",
            filename=export_filename,
            headers={"Content-Disposition": f'attachment; filename="{export_filename}"'}
        )

    elif fmt in ("mp3_320", "mp3-320", "mp3"):
        export_filename = f"{source_stem}_320kbps.mp3"
        target_path = str(processed_dir / export_filename)
        if not os.path.exists(target_path):
            temp_wav = str(processed_dir / f"{source_stem}_temp_mp3.wav")
            try:
                data, sr = sf.read(abs_path, dtype="float32", always_2d=False)
                sf.write(temp_wav, data, sr, subtype="PCM_24", format="WAV")
                cmd = ["ffmpeg", "-y", "-i", temp_wav, "-codec:a", "libmp3lame", "-b:a", "320k", target_path]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if res.returncode != 0:
                    sf.write(target_path, data, sr, subtype="PCM_16")
            finally:
                if os.path.exists(temp_wav):
                    os.remove(temp_wav)
        return FileResponse(
            target_path,
            media_type="audio/mpeg",
            filename=export_filename,
            headers={"Content-Disposition": f'attachment; filename="{export_filename}"'}
        )

    else:
        # Default fallback
        media_type = f"audio/{output.file_format}" if output.file_format != "mp3" else "audio/mpeg"
        return FileResponse(
            abs_path,
            media_type=media_type,
            filename=output.filename,
            headers={"Content-Disposition": f'attachment; filename="{output.filename}"'}
        )

@router.get("/{output_id}/stream")
def stream_output_file(output_id: str, db: Session = Depends(get_db)):
    output = db.query(AudioOutput).filter(AudioOutput.id == output_id).first()
    if not output:
        raise HTTPException(status_code=404, detail="Audio output not found")

    abs_path = os.path.join(settings.BASE_DIR, output.storage_relative_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File missing from storage")

    media_type = f"audio/{output.file_format}" if output.file_format != "mp3" else "audio/mpeg"
    return FileResponse(abs_path, media_type=media_type, filename=output.filename)

@router.delete("/{output_id}", status_code=status.HTTP_200_OK)
def delete_output_file(output_id: str, db: Session = Depends(get_db)):
    output = db.query(AudioOutput).filter(AudioOutput.id == output_id).first()
    if not output:
        raise HTTPException(status_code=404, detail="Audio output not found")

    abs_path = os.path.join(settings.BASE_DIR, output.storage_relative_path)
    if os.path.exists(abs_path):
        try:
            os.remove(abs_path)
        except OSError:
            pass

    db.delete(output)
    db.commit()
    return {"message": "Audio output deleted successfully", "output_id": output_id}
