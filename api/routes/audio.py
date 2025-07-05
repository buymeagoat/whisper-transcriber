from __future__ import annotations

import subprocess
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile, HTTPException

from api.paths import storage, UPLOAD_DIR
from api.errors import ErrorCode, http_error
from api.app_state import backend_log

ALLOWED_FORMATS = {"mp3", "m4a", "wav", "flac"}

router = APIRouter()


@router.post("/convert")
async def convert_audio(
    file: UploadFile = File(...), target_format: str = Form(...)
) -> dict[str, str]:
    if target_format not in ALLOWED_FORMATS:
        raise http_error(ErrorCode.UNSUPPORTED_MEDIA)

    file_id = uuid.uuid4().hex
    safe_name = Path(file.filename).name
    saved_name = f"{file_id}_{safe_name}"
    try:
        src_path = storage.save_upload(file.file, saved_name)
    except HTTPException:
        raise
    except OSError as e:
        backend_log.error(f"Failed to save upload '{saved_name}': {e}")
        raise http_error(ErrorCode.FILE_SAVE_FAILED) from e

    dest_name = f"{Path(safe_name).stem}_{file_id}.{target_format}"
    dest_path = UPLOAD_DIR / dest_name
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(src_path), str(dest_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        backend_log.error(f"ffmpeg convert failed: {e}")
        dest_path.unlink(missing_ok=True)
        storage.delete_upload(src_path.name)
        raise http_error(ErrorCode.UNSUPPORTED_MEDIA) from e

    return {"path": str(dest_path)}


@router.post("/edit")
async def edit_audio(
    file: UploadFile = File(...),
    trim_start: float | None = Form(None),
    trim_end: float | None = Form(None),
    volume: float | None = Form(None),
) -> dict[str, str]:
    """Perform basic editing on the uploaded audio file."""

    file_id = uuid.uuid4().hex
    safe_name = Path(file.filename).name
    saved_name = f"{file_id}_{safe_name}"
    try:
        src_path = storage.save_upload(file.file, saved_name)
    except HTTPException:
        raise
    except OSError as e:
        backend_log.error(f"Failed to save upload '{saved_name}': {e}")
        raise http_error(ErrorCode.FILE_SAVE_FAILED) from e

    dest_name = f"{Path(safe_name).stem}_{file_id}{Path(safe_name).suffix}"
    dest_path = UPLOAD_DIR / dest_name

    cmd = ["ffmpeg", "-y", "-i", str(src_path)]
    if trim_start is not None:
        cmd.extend(["-ss", str(trim_start)])
    if trim_end is not None:
        cmd.extend(["-to", str(trim_end)])
    if volume is not None:
        cmd.extend(["-filter:a", f"volume={volume}"])
    cmd.append(str(dest_path))

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        backend_log.error(f"ffmpeg edit failed: {e}")
        dest_path.unlink(missing_ok=True)
        storage.delete_upload(src_path.name)
        raise http_error(ErrorCode.UNSUPPORTED_MEDIA) from e

    return {"path": str(dest_path)}
