from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from api.errors import ErrorCode, http_error
from api.paths import storage, TRANSCRIPTS_DIR
from api.app_state import backend_log
from api.services.jobs import get_job
from api.exporters import srt_to_txt

import pyttsx3

router = APIRouter()


@router.post("/tts/{job_id}")
def generate_tts(job_id: str) -> dict[str, str]:
    job = get_job(job_id)
    if not job:
        raise http_error(ErrorCode.JOB_NOT_FOUND)

    if not job.transcript_path:
        raise http_error(ErrorCode.FILE_NOT_FOUND)

    transcript_file = Path(job.transcript_path)
    if not transcript_file.exists():
        raise http_error(ErrorCode.FILE_NOT_FOUND)

    text = srt_to_txt(transcript_file)

    out_dir = storage.get_transcript_dir(job_id) / "tts_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "speech.wav"

    try:
        engine = pyttsx3.init()
    except Exception as e:  # pragma: no cover - engine init failure
        backend_log.error(f"pyttsx3 init failed: {e}", exc_info=True)
        raise http_error(ErrorCode.WHISPER_RUNTIME) from e

    try:
        engine.save_to_file(text, str(out_path))
        engine.runAndWait()
    except Exception as e:  # pragma: no cover - engine runtime failure
        backend_log.error(f"pyttsx3 synthesis failed: {e}", exc_info=True)
        raise http_error(ErrorCode.WHISPER_RUNTIME) from e

    rel_path = f"/transcripts/{job_id}/tts_output/{out_path.name}"
    return {"path": rel_path}
