from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from api.errors import ErrorCode, http_error
from api.paths import storage, TRANSCRIPTS_DIR
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

    engine = pyttsx3.init()
    engine.save_to_file(text, str(out_path))
    engine.runAndWait()

    rel_path = f"/transcripts/{job_id}/tts_output/{out_path.name}"
    return {"path": rel_path}
