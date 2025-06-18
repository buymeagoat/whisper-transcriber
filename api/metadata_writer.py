import json
import re
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from api.orm_bootstrap import SessionLocal
from api.models import TranscriptMetadata
from api.utils.logger import get_logger

TRANSCRIPTS_DIR = Path(__file__).parent.parent / "transcripts"

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())

def run_metadata_writer(
    job_id: str,
    transcript_path: Path,
    duration_sec: float,
    sample_rate: int,
    db_lock: threading.Lock
):
    logger = get_logger(job_id)

    txt_path = transcript_path
    if not txt_path.exists():
        logger.warning(f"Transcript path does not exist: {txt_path}")
        text = ""
    else:
        text = clean_text(txt_path.read_text(encoding="utf-8"))

    tokens = len(text.split())
    abstract = f"{text[:500]}..." if text else "*No content*"

    metadata_dict = {
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
    output_path.write_text(json.dumps(metadata_dict, indent=2), encoding="utf-8")

    logger.info(f"[{job_id}] metadata_writer wrote {output_path}")
    logger.info(f"[{job_id}] transcript_txt_path exists: {txt_path.exists()}")
    logger.info(f"[{job_id}] abstract preview: {abstract[:80]}")

    # Write to database via SQLAlchemy ORM
    try:
        with db_lock:
            with SessionLocal() as session:
                session.merge(TranscriptMetadata(
                    job_id=job_id,
                    tokens=tokens,
                    duration=duration_sec,
                    abstract=abstract,
                    sample_rate=sample_rate,
                    generated_at=datetime.fromisoformat(metadata_dict["generated_at"]),
                ))
                session.commit()
                logger.info(f"[{job_id}] metadata inserted via ORM")
    except Exception as e:
        logger.exception(f"[{job_id}] ERROR inserting metadata into DB")
        raise
