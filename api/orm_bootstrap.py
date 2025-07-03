import subprocess
import os
import time
import logging
from pathlib import Path

from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from api.models import Base
from api.utils.logger import get_logger
from api.settings import settings

DB_URL = settings.db_url
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)

log = get_logger("orm")


def validate_or_initialize_database():
    log.info("Bootstrapping database...")

    # ── Step 1: Check database connection with retries ──
    max_attempts = settings.db_connect_attempts
    for attempt in range(1, max_attempts + 1):
        log.info("Attempting database connection (%s/%s)...", attempt, max_attempts)
        try:
            with engine.connect():
                break
        except OperationalError as exc:
            if attempt == max_attempts:
                log.critical(
                    "Database unreachable after %s attempts. Ensure a PostgreSQL service is running and DB_URL is correct.",
                    max_attempts,
                )
                log.critical("Last error: %s", exc)
                raise RuntimeError("Database unreachable")
            wait_time = attempt
            log.warning(
                "Database connection failed (attempt %s/%s). Retrying in %s second(s)...",
                attempt,
                max_attempts,
                wait_time,
            )
            if log.isEnabledFor(logging.DEBUG):
                log.debug("Connection error: %s", exc)
            time.sleep(wait_time)

    # ── Step 2: Run Alembic migrations ──
    log.info("Running Alembic migrations to ensure schema is current...")
    ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"
    try:
        env = os.environ.copy()
        env.update({"PYTHONPATH": str(Path(__file__).resolve().parent.parent)})
        completed = subprocess.run(
            ["alembic", "-c", str(ALEMBIC_INI), "upgrade", "head"],
            check=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if log.isEnabledFor(logging.DEBUG):
            if completed.stdout:
                log.debug("Alembic STDOUT:\n%s", completed.stdout)
            if completed.stderr:
                log.debug("Alembic STDERR:\n%s", completed.stderr)
        log.info("Alembic migrations applied successfully.")
    except subprocess.CalledProcessError as e:
        log.critical("Alembic failed with exit code %s", e.returncode)
        if e.stdout:
            log.critical("Alembic STDOUT:\n%s", e.stdout)
        if e.stderr:
            log.critical("Alembic STDERR:\n%s", e.stderr)
        raise RuntimeError("Alembic migrations failed") from e

    # ── Step 3: Validate expected tables exist ──
    inspector = inspect(engine)
    expected = set(Base.metadata.tables.keys())
    actual = set(inspector.get_table_names())

    if not expected.issubset(actual):
        log.critical(f"Schema mismatch: expected {expected}, found {actual}")
        log.critical("Schema invalid or incomplete.")
        raise RuntimeError("Database schema invalid")

    # ── Step 4: Success ──
    log.info("Database bootstrapping complete — schema verified.")
