import os
import shutil
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from subprocess import Popen, PIPE
from typing import Union
from zoneinfo import ZoneInfo

from api.metadata_writer import run_metadata_writer
from api.models import Job, JobStatusEnum
from api.paths import (
    storage,
    UPLOAD_DIR,
    TRANSCRIPTS_DIR,
    MODEL_DIR,
    LOG_DIR,
)

# ─── Paths ─── (imported from api.paths)

# ─── Config ───
LOCAL_TZ = ZoneInfo("America/Chicago")
from api.settings import settings
from api.services.job_queue import JobQueue, ThreadJobQueue, BrokerJobQueue

from api.utils.logger import get_logger

backend_log = get_logger("backend")
ACCESS_LOG = LOG_DIR / "access.log"

# ─── Whisper CLI Check ───
WHISPER_BIN = shutil.which("whisper")

# ─── DB Lock ───
db_lock = threading.RLock()

# ─── Job Queue ───
if settings.job_queue_backend == "thread":
    job_queue: JobQueue = ThreadJobQueue(settings.max_concurrent_jobs)
else:
    job_queue = BrokerJobQueue()


def get_duration(path: Union[str, os.PathLike]) -> float:
    if shutil.which("ffprobe") is None:
        raise RuntimeError("ffprobe not found in PATH. Required to determine duration.")

    try:
        out = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return float(out.stdout.strip())
    except Exception:
        return 0.0


def handle_whisper(
    job_id: str, upload: Path, job_dir: Path, model: str, *, start_thread: bool = True
):
    from api.orm_bootstrap import SessionLocal

    global WHISPER_BIN
    WHISPER_BIN = WHISPER_BIN or shutil.which("whisper")
    if not WHISPER_BIN:
        raise RuntimeError(
            "Whisper CLI not found in PATH. Is it installed and in the environment?"
        )

    with db_lock:
        with SessionLocal() as db:
            job = db.query(Job).filter_by(id=job_id).first()
            if job:
                job.status = JobStatusEnum.PROCESSING
                job.started_at = datetime.utcnow()
                db.commit()

    def _run():
        log_path = LOG_DIR / f"{job_id}.log"
        logger = get_logger(job_id)
        logger.info("_run() started")

        try:
            job_dir.mkdir(parents=True, exist_ok=True)
            output_filename = Path(upload).stem + ".srt"

            cmd = [
                WHISPER_BIN,
                str(upload),
                "--model",
                model,
                "--model_dir",
                str(MODEL_DIR),
                "--output_dir",
                str(job_dir),
                "--output_format",
                "srt",
                "--language",
                "en",
                "--verbose",
                "True",
            ]
            logger.info(f"Launching subprocess: {' '.join(cmd)}")
            logger.info(f"FINAL CMD: {' '.join(cmd)}")

            try:
                with Popen(cmd, stdout=PIPE, stderr=PIPE, text=True, bufsize=1) as proc:

                    def stream_output(stream, label):
                        for line in iter(stream.readline, ""):
                            logger.info(f"{label}: {line.strip()}")

                    stdout_thread = threading.Thread(
                        target=stream_output, args=(proc.stdout, "STDOUT")
                    )
                    stderr_thread = threading.Thread(
                        target=stream_output, args=(proc.stderr, "STDERR")
                    )
                    stdout_thread.start()
                    stderr_thread.start()

                    proc.wait()
                    stdout_thread.join()
                    stderr_thread.join()
                    logger.info(f"Whisper exited with code {proc.returncode}")

            except subprocess.TimeoutExpired:
                logger.error("Whisper timed out")
                proc.kill()
                with db_lock:
                    with SessionLocal() as db:
                        job = db.query(Job).filter_by(id=job_id).first()
                        if job:
                            job.status = JobStatusEnum.FAILED_TIMEOUT
                            job.log_path = str(log_path)
                            job.finished_at = datetime.utcnow()
                            db.commit()
                return

            except Exception as e:
                logger.error(f"Subprocess launch failed: {e}")
                with db_lock:
                    with SessionLocal() as db:
                        job = db.query(Job).filter_by(id=job_id).first()
                        if job:
                            job.status = JobStatusEnum.FAILED_LAUNCH_ERROR
                            job.log_path = str(log_path)
                            job.finished_at = datetime.utcnow()
                            db.commit()
                return

            raw_txt_path = job_dir / (Path(upload).with_suffix(".srt").name)
            if not raw_txt_path.exists():
                raise RuntimeError(
                    f"[{job_id}] Expected .srt not found at {raw_txt_path}"
                )

            with db_lock:
                with SessionLocal() as db:
                    if proc.returncode == 0:
                        try:
                            logger.info("Starting metadata_writer...")
                            duration = get_duration(upload)
                            job = db.query(Job).filter_by(id=job_id).first()
                            if job:
                                job.status = JobStatusEnum.ENRICHING
                                db.commit()
                                run_metadata_writer(
                                    job_id,
                                    raw_txt_path,
                                    duration,
                                    16000,
                                    db_lock,  # type: ignore[arg-type]
                                )
                                logger.info("metadata_writer complete.")
                                with SessionLocal() as db2:  # NEW clean session
                                    job2 = db2.query(Job).filter_by(id=job_id).first()
                                    if job2:
                                        job2.status = JobStatusEnum.COMPLETED
                                        job2.transcript_path = str(raw_txt_path)
                                        job2.finished_at = datetime.utcnow()
                                        db2.commit()
                                        logger.info(
                                            "status -> COMPLETED committed"
                                        )  # debug breadcrumb
                        except Exception as e:
                            job = db.query(Job).filter_by(id=job_id).first()
                            if job:
                                job.status = JobStatusEnum.FAILED_UNKNOWN
                                job.log_path = str(log_path)
                                job.finished_at = datetime.utcnow()
                                logger.error(f"Metadata writer failed: {e}")
                                db.commit()
                    elif proc.returncode < 0:
                        logger.error(
                            f"Whisper process terminated with signal {-proc.returncode}"
                        )
                        job = db.query(Job).filter_by(id=job_id).first()
                        if job:
                            job.status = JobStatusEnum.FAILED_WHISPER_ERROR
                            job.log_path = str(log_path)
                            job.finished_at = datetime.utcnow()
                            db.commit()
                        logger.error(
                            f"Whisper process terminated with signal {-proc.returncode}"
                        )
                    else:
                        logger.error("Whisper process failed — not zero return code")
                        job = db.query(Job).filter_by(id=job_id).first()
                        if job:
                            job.status = JobStatusEnum.FAILED_WHISPER_ERROR
                            job.log_path = str(log_path)
                            job.finished_at = datetime.utcnow()
                            db.commit()
        except Exception as e:
            logger.critical(f"CRITICAL thread error: {e}")
            with db_lock:
                with SessionLocal() as db:
                    job = db.query(Job).filter_by(id=job_id).first()
                    if job:
                        job.status = JobStatusEnum.FAILED_THREAD_EXCEPTION
                        job.log_path = str(log_path)
                        job.finished_at = datetime.utcnow()
                        db.commit()

    if start_thread:
        threading.Thread(target=_run, daemon=True).start()
    else:
        _run()
