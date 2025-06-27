from __future__ import annotations

import subprocess
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile

from api.paths import storage, UPLOAD_DIR
from api.errors import ErrorCode, http_error

ALLOWED_FORMATS = {"mp3", "m4a", "wav", "flac"}

router = APIRouter()


@router.post("/convert")
async def convert_audio(
    file: UploadFile = File(...), target_format: str = Form(...)
) -> dict[str, str]:
    if target_format not in ALLOWED_FORMATS:
        raise http_error(ErrorCode.UNSUPPORTED_MEDIA)

    file_id = uuid.uuid4().hex
    saved_name = f"{file_id}_{file.filename}"
    try:
        src_path = storage.save_upload(file.file, saved_name)
    except Exception:
        raise http_error(ErrorCode.FILE_SAVE_FAILED)

    dest_name = f"{Path(file.filename).stem}_{file_id}.{target_format}"
    dest_path = UPLOAD_DIR / dest_name
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(src_path), str(dest_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception:
        raise http_error(ErrorCode.UNSUPPORTED_MEDIA)

    return {"path": str(dest_path)}
