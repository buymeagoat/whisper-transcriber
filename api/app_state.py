import os
import shutil
import subprocess
import threading
from datetime import datetime, timedelta
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
from api.settings import settings

LOCAL_TZ = ZoneInfo(settings.timezone)
from api.services.job_queue import JobQueue, ThreadJobQueue, BrokerJobQueue

from api.utils.logger import get_logger
from api.routes.progress import send_progress_update

backend_log = get_logger("backend")
ACCESS_LOG = LOG_DIR / "access.log"

# ─── Whisper CLI Check ───
WHISPER_BIN = shutil.which(settings.whisper_bin)

# ─── DB Lock ───
from api.utils.db_lock import db_lock

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
    WHISPER_BIN = WHISPER_BIN or shutil.which(settings.whisper_bin)
    if not WHISPER_BIN:
        raise RuntimeError(
            "Whisper CLI not found in PATH. Is it installed and in the environment?"
        )

    # Notify clients that the job is queued
    send_progress_update(job_id, JobStatusEnum.QUEUED.value)

    with db_lock:
        with SessionLocal() as db:
            job = db.query(Job).filter_by(id=job_id).first()
            if job:
                job.status = JobStatusEnum.PROCESSING
                job.started_at = datetime.utcnow()
                db.commit()
                send_progress_update(job_id, JobStatusEnum.PROCESSING.value)

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
                settings.whisper_language,
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
                            send_progress_update(
                                job_id, JobStatusEnum.FAILED_TIMEOUT.value
                            )
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
                            send_progress_update(
                                job_id, JobStatusEnum.FAILED_LAUNCH_ERROR.value
                            )
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
                                send_progress_update(
                                    job_id, JobStatusEnum.ENRICHING.value
                                )
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
                                        send_progress_update(
                                            job_id, JobStatusEnum.COMPLETED.value
                                        )
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
                                send_progress_update(
                                    job_id, JobStatusEnum.FAILED_UNKNOWN.value
                                )
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
                            send_progress_update(
                                job_id, JobStatusEnum.FAILED_WHISPER_ERROR.value
                            )
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
                            send_progress_update(
                                job_id, JobStatusEnum.FAILED_WHISPER_ERROR.value
                            )
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
                        send_progress_update(
                            job_id, JobStatusEnum.FAILED_THREAD_EXCEPTION.value
                        )

    if start_thread:
        threading.Thread(target=_run, daemon=True).start()
    else:
        _run()


def cleanup_once() -> None:
    """Remove uploads, transcripts and logs older than the configured age."""
    if not settings.cleanup_enabled:
        return

    cutoff = datetime.utcnow() - timedelta(days=settings.cleanup_days)

    for file in UPLOAD_DIR.glob("*"):
        if file.is_file() and datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
            storage.delete_upload(file.name)

    for directory in TRANSCRIPTS_DIR.iterdir():
        if (
            directory.is_dir()
            and datetime.fromtimestamp(directory.stat().st_mtime) < cutoff
        ):
            storage.delete_transcript_dir(directory.name)

    for file in LOG_DIR.glob("*"):
        try:
            if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
                if file.is_file():
                    file.unlink()
                else:
                    shutil.rmtree(file, ignore_errors=True)
        except FileNotFoundError:
            pass


def _cleanup_task(interval: int = settings.cleanup_interval_seconds) -> None:
    while True:
        cleanup_once()
        threading.Event().wait(interval)


def start_cleanup_thread(interval: int = settings.cleanup_interval_seconds) -> None:
    threading.Thread(target=_cleanup_task, args=(interval,), daemon=True).start()
