import json
import re
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from sqlalchemy.engine.url import make_url
from api.utils.logger import get_logger

TRANSCRIPTS_DIR = Path(__file__).parent.parent / "transcripts"

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())

def run_metadata_writer(
    job_id: str,
    transcript_txt_path: Path,
    duration_sec: float,
    sample_rate: Optional[int] = None,
    db_lock: Optional[object] = None,  # Unused in MVP
) -> None:
    logger = get_logger(job_id)

    txt_path = Path(transcript_txt_path)

    if not txt_path.exists():
        logger.warning(f"Transcript path does not exist: {txt_path}")
        text = ""
    else:
        text = clean_text(txt_path.read_text(encoding="utf-8"))

    tokens = len(text.split())
    abstract = f"{text[:500]}..." if text else "*No content*"

    metadata = {
        "job_id": job_id,
        "tokens": tokens,
        "duration": duration_sec,
        "abstract": abstract,
        "sample_rate": sample_rate,
        "generated_at": datetime.utcnow().isoformat(),
    }

    # Write metadata.json to transcript directory
    job_dir = TRANSCRIPTS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    output_path = job_dir / "metadata.json"
    output_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    logger.info(f"[{job_id}] metadata_writer wrote {output_path}")
    logger.info(f"[{job_id}] transcript_txt_path exists: {txt_path.exists()}")
    logger.info(f"[{job_id}] abstract preview: {abstract[:80]}")

    # Get SQLite DB path from URL string
    db_url = os.environ.get("DB", "sqlite:///api/jobs.db")
    db_path = make_url(db_url).database
    if not db_path:
        raise RuntimeError(f"[{job_id}] ERROR: Could not extract DB path from URL: {db_url}")

    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO metadata (
                    job_id, tokens, duration, abstract,
                    sample_rate, generated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    tokens,
                    duration_sec,
                    abstract,
                    sample_rate,
                    metadata["generated_at"]
                )
            )
            conn.commit()
            logger.info(f"[{job_id}] metadata inserted into DB: {db_path}")
    except Exception as e:
        logger.info(f"[{job_id}] ERROR inserting metadata into DB: {e}")
