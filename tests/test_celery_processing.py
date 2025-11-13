"""Celery worker regression tests covering the transcription task."""

from __future__ import annotations

import io
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from api.models import Job, JobStatusEnum
from api.orm_bootstrap import SessionLocal
from api.services.app_worker import transcribe_audio
from api.worker import celery_app
from api.paths import storage


@pytest.mark.asyncio
async def test_celery_transcription_task_updates_job(async_client, admin_token, security_headers, stub_job_queue, monkeypatch):
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

    model_path = storage.models_dir / "small.pt"
    model_path.write_bytes(b"fake model contents")

    loaded_models: list[tuple[str, str | None]] = []

    class _StubModel:
        def __init__(self) -> None:
            self.device: str | None = None
            self.transcribe_called_with: str | None = None

        def to(self, device: str) -> "_StubModel":
            self.device = device
            return self

        def transcribe(self, audio_file: str):
            self.transcribe_called_with = audio_file
            return {"text": "stub transcript"}

    stub_model = _StubModel()

    def _fake_load_model(path: str, *, download_root: str | None = None) -> _StubModel:
        loaded_models.append((path, download_root))
        return stub_model

    monkeypatch.setitem(sys.modules, "whisper", SimpleNamespace(load_model=_fake_load_model))
    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False)),
    )

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
        assert contents == "stub transcript"

    assert loaded_models == [("small", str(storage.models_dir))]
    assert stub_model.transcribe_called_with == str(audio_path)
