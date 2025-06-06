"""
Shared fixtures for backend test-suite.
Sets up in-memory DB, stubs long-running tasks, and provides job submission helpers.
"""
import os
import sys
import subprocess
import sqlite3
import shutil
from pathlib import Path
from typing import Callable, Generator
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

# ── Project imports ──
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api.main import app, TRANSCRIPTS_DIR, DB_PATH


# ── Configure shared in-memory DB ──
os.environ["DB"] = "sqlite:///file:memory?mode=memory&cache=shared"


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations() -> None:
    """Run Alembic against shared in-memory DB."""
    subprocess.run(["alembic", "upgrade", "head"], check=True)


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def _stub_duration(monkeypatch):
    import api.main as m
    monkeypatch.setattr(m, "get_duration", lambda *a, **kw: 30.0)


@pytest.fixture
def submit_stub_job(
    tmp_path, monkeypatch
) -> Generator[Callable[[TestClient, str], str], None, None]:
    """Returns a function to submit a fake audio job and simulate transcription."""

    def _factory(client: TestClient, filename: str = "ingest.wav") -> str:
        from pathlib import Path

        def fake_popen(cmd, *a, **kw):
            job_dir = Path(cmd[cmd.index("--output_dir") + 1])
            job_dir.mkdir(parents=True, exist_ok=True)
            (job_dir / "ingest.txt").write_text("stub transcript")
            (job_dir / "ingest.json").write_text("{}")
            return Mock(stdout=["\n"], wait=lambda: 0, __enter__=lambda s: s, __exit__=lambda *x: None)

        def fake_writer(job_id, transcript_path, **_):
            meta = transcript_path.with_suffix(".json")
            meta.write_text('{"tokens": 2, "duration": 30.0}')
            con = sqlite3.connect(DB_PATH)
            con.execute(
                "UPDATE jobs SET status='completed', transcript_path=? WHERE id=?",
                (str(transcript_path.resolve()), job_id)
            )
            con.execute(
                "INSERT OR REPLACE INTO metadata (job_id, tokens, duration) VALUES (?, ?, ?)",
                (job_id, 2, 30.0)
            )
            con.commit()
            con.close()
            return meta

        monkeypatch.setattr("api.main.Popen", fake_popen)
        monkeypatch.setattr("api.main.run_metadata_writer", fake_writer)

        wav = tmp_path / filename
        wav.write_bytes(b"\0\0")
        return client.post(
            "/jobs", files={"file": (filename, wav.open("rb"), "audio/wav")}, data={"model": "base", "ingest": "true"}
        ).json()["job_id"]

    yield _factory

    if TRANSCRIPTS_DIR.exists():
        shutil.rmtree(TRANSCRIPTS_DIR, ignore_errors=True)
