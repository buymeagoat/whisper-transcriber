import json
import uuid
import sqlite3
import os
from pathlib import Path

from api.metadata_writer import run_metadata_writer
from api.main import DB_PATH, TRANSCRIPTS_DIR


def test_metadata_writer(tmp_path):
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    job_id = uuid.uuid4().hex
    from sqlalchemy.engine.url import make_url

    # Ensure we use the correct DB path Alembic applies migrations to
    url_obj = make_url(os.environ.get("DB", "sqlite:///api/jobs.db"))
    db_path = url_obj.database or "api/jobs.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """INSERT INTO jobs (id, status, original_filename, saved_filename, model, created_at)
           VALUES (?, ?, ?, ?, ?, datetime('now'))""",
        (job_id, "completed", "test.wav", f"{job_id}.wav", "base")
    )
    conn.commit()

    job_dir = Path(TRANSCRIPTS_DIR) / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    raw_txt = job_dir / "raw.txt"
    raw_txt.write_text("test metadata output", encoding="utf-8")

    run_metadata_writer(job_id, raw_txt, duration_sec=30.0, sample_rate=16000)

    meta_path = raw_txt.with_suffix(".json")
    assert meta_path.exists()
    with open(meta_path) as f:
        meta = json.load(f)
    assert meta["tokens"] == 3
