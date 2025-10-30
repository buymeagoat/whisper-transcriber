"""Celery worker regression tests covering the transcription task."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from api.models import Job, JobStatusEnum
from api.orm_bootstrap import SessionLocal
from api.services.app_worker import transcribe_audio
from api.worker import celery_app


@pytest.mark.asyncio
async def test_celery_transcription_task_updates_job(async_client, admin_token, security_headers, stub_job_queue):
    """Executing the Celery task should mark the job complete and persist a transcript."""

    upload = await async_client.post(
        "/jobs/",
        data={"model": "small"},
        files={"file": ("celery.wav", io.BytesIO(b"celery audio"), "audio/wav")},
        headers=security_headers(token=admin_token),
    )
    assert upload.status_code == 200, upload.text
    job_id = upload.json()["job_id"]

    with SessionLocal() as session:
        job = session.get(Job, job_id)
        assert job is not None
        audio_path = Path(job.saved_filename)

    previous_always_eager = celery_app.conf.task_always_eager
    previous_store = celery_app.conf.task_store_eager_result
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_store_eager_result = True
    try:
        result = transcribe_audio.apply(args=(job_id,), kwargs={"audio_path": str(audio_path)})
        payload = result.get(timeout=5)
    finally:
        celery_app.conf.task_always_eager = previous_always_eager
        celery_app.conf.task_store_eager_result = previous_store

    assert payload["status"] == "completed"
    assert payload["job_id"] == job_id

    with SessionLocal() as session:
        refreshed = session.get(Job, job_id)
        assert refreshed is not None
        assert refreshed.status == JobStatusEnum.COMPLETED
        assert refreshed.transcript_path is not None
        transcript_file = Path(refreshed.transcript_path)
        assert transcript_file.exists()
        contents = transcript_file.read_text(encoding="utf-8")
        assert "Bytes:" in contents
