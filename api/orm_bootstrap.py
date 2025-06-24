import subprocess
import sys
import os

from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import sessionmaker
from api.models import Base
from api.utils.logger import get_logger

DB_PATH = os.getenv("DB", "api/jobs.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

log = get_logger("orm")


def validate_or_initialize_database():
    log.info("Bootstrapping database...")

    # ── Step 1: Create DB file if missing ──
    if not os.path.exists(DB_PATH):
        log.info("jobs.db does not exist — creating empty file.")
        open(DB_PATH, "a").close()

    # ── Step 2: Run Alembic migrations ──
    log.info("Running Alembic migrations to ensure schema is current...")
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        log.info("Alembic migrations applied successfully.")
    except subprocess.CalledProcessError as e:
        log.critical(f"Alembic failed to apply migrations: {e}")
        log.critical(f"Alembic error: {e}")
        sys.exit(1)

    # ── Step 3: Validate expected tables exist ──
    inspector = inspect(engine)
    expected = set(Base.metadata.tables.keys())
    actual = set(inspector.get_table_names())

    if not expected.issubset(actual):
        log.critical(f"Schema mismatch: expected {expected}, found {actual}")
        log.critical("Schema invalid or incomplete.")
        sys.exit(1)

    # ── Step 4: Success ──
    log.info("Database bootstrapping complete — schema verified.")
