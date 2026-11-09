import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

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
def download_output_file(output_id: str, db: Session = Depends(get_db)):
    output = db.query(AudioOutput).filter(AudioOutput.id == output_id).first()
    if not output:
        raise HTTPException(status_code=404, detail="Audio output not found")

    abs_path = os.path.join(settings.BASE_DIR, output.storage_relative_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File missing from storage")

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
