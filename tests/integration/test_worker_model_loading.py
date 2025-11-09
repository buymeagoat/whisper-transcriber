"""Integration test verifying the worker loads Whisper checkpoints."""

from __future__ import annotations

import sys
import pytest
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from api.app_worker import bootstrap_model_assets
from api.models import Job, JobStatusEnum
from api.orm_bootstrap import SessionLocal
from api.paths import storage
from api.services.app_worker import transcribe_audio


def test_transcribe_audio_uses_fixture_model(tmp_path, monkeypatch) -> None:
    models_dir = storage.models_dir
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / "integration.pt"
    model_path.write_bytes(b"fixture model")

    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"fake audio data")

    job_id = str(uuid4())
    with SessionLocal() as session:
        job = Job(
            id=job_id,
            original_filename="sample.wav",
            saved_filename=str(audio_path),
            model="integration",
            status=JobStatusEnum.QUEUED,
        )
        session.add(job)
        session.commit()

    load_calls: list[tuple[str, str | None]] = []

    class _StubModel:
        def __init__(self) -> None:
            self.device: str | None = None
            self.transcribe_called_with: str | None = None

        def to(self, device: str) -> "_StubModel":
            self.device = device
            return self

        def transcribe(self, audio_file: str):
            self.transcribe_called_with = audio_file
            return {"text": "integration transcript"}

    stub_model = _StubModel()

    def _fake_load_model(name: str, *, download_root: str | None = None) -> _StubModel:
        load_calls.append((name, download_root))
        return stub_model

    monkeypatch.setitem(sys.modules, "whisper", SimpleNamespace(load_model=_fake_load_model))
    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False)),
    )

    bootstrap_model_assets()

    result = transcribe_audio.run(job_id, audio_path=str(audio_path))
    assert result["status"] == "completed"
    assert result["job_id"] == job_id

    transcript_path = Path(result["transcript_path"])
    assert transcript_path.exists()
    assert transcript_path.read_text(encoding="utf-8") == "integration transcript"

    assert load_calls == [("integration", str(storage.models_dir))]
    assert stub_model.transcribe_called_with == str(audio_path)


def test_transcribe_audio_failure_records_log(tmp_path) -> None:
    audio_path = tmp_path / "missing.wav"
    audio_path.write_bytes(b"fake audio data")

    job_id = str(uuid4())
    with SessionLocal() as session:
        job = Job(
            id=job_id,
            original_filename="missing.wav",
            saved_filename=str(audio_path),
            model="missing-model",
            status=JobStatusEnum.QUEUED,
        )
        session.add(job)
        session.commit()

    # Ensure no model checkpoint exists to force the failure path.
    models_dir = storage.models_dir
    models_dir.mkdir(parents=True, exist_ok=True)
    for child in models_dir.glob("*.pt"):
        child.unlink()
    # Seed bootstrap with an unrelated checkpoint so no downloads occur.
    (models_dir / "bootstrap.pt").write_bytes(b"placeholder")

    with SessionLocal() as session:
        job = session.get(Job, job_id)
        assert job is not None
        job.model = "nonexistent"
        session.commit()

    with pytest.raises(FileNotFoundError):
        transcribe_audio.run(job_id, audio_path=str(audio_path))

    with SessionLocal() as session:
        job = session.get(Job, job_id)
        assert job is not None
        assert job.status == JobStatusEnum.FAILED
        assert job.log_path is not None
        log_contents = Path(job.log_path).read_text(encoding="utf-8")
        assert "Model file not found" in log_contents
