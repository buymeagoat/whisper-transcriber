import subprocess
import sys
import os
from pathlib import Path

from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from api.models import Base
from api.utils.logger import get_logger
from api.settings import settings

DB_URL = settings.db_url
engine_kwargs = {}
if DB_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
engine = create_engine(DB_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine)

log = get_logger("orm")


def validate_or_initialize_database():
    log.info("Bootstrapping database...")

    # ── Step 1: Create DB file if using SQLite and file missing ──
    if DB_URL.startswith("sqlite"):
        db_path = DB_URL.split("sqlite:///", 1)[-1]
        if not os.path.exists(db_path):
            log.info("jobs.db does not exist — creating empty file.")
            open(db_path, "a").close()

    # ── Step 2: Check database connection ──
    try:
        with engine.connect():
            pass
    except OperationalError:
        log.critical(
            "Database unreachable. Use DB=/path/to/jobs.db for SQLite or start a PostgreSQL service."
        )
        sys.exit(1)

    # ── Step 3: Run Alembic migrations ──
    log.info("Running Alembic migrations to ensure schema is current...")
    ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"
    try:
        env = os.environ.copy()
        env.update({"PYTHONPATH": str(Path(__file__).resolve().parent.parent)})
        subprocess.run(
            ["alembic", "-c", str(ALEMBIC_INI), "upgrade", "head"],
            check=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        log.info("Alembic migrations applied successfully.")
    except subprocess.CalledProcessError as e:
        log.critical(f"Alembic failed to apply migrations: {e}")
        if e.stdout:
            log.critical(e.stdout)
        if e.stderr:
            log.critical(e.stderr)
        sys.exit(1)

    # ── Step 4: Validate expected tables exist ──
    inspector = inspect(engine)
    expected = set(Base.metadata.tables.keys())
    actual = set(inspector.get_table_names())

    if not expected.issubset(actual):
        log.critical(f"Schema mismatch: expected {expected}, found {actual}")
        log.critical("Schema invalid or incomplete.")
        sys.exit(1)

    # ── Step 5: Success ──
    log.info("Database bootstrapping complete — schema verified.")
