# NOTE: This module is unused and will be removed in a future release.
"""Deprecated module kept for backward compatibility.

Use :mod:`api.settings` instead. This file now simply loads environment
variables the old way so legacy imports keep working. New code should import
``settings`` from ``api.settings``.
"""

import os
import logging
import sys
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

# Raw environment variable for API host
RAW_VITE_API_HOST = os.getenv("VITE_API_HOST")
API_HOST = RAW_VITE_API_HOST or "http://localhost:8000"

# PostgreSQL is required. Provide ``DB_URL`` with the connection string to your
# PostgreSQL server. Using a different engine is only recommended for local
# development or testing.
DB_URL = os.getenv(
    "DB_URL",
    "postgresql+psycopg2://whisper:whisper@db:5432/whisper",
)

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
LOG_TO_STDOUT = os.getenv("LOG_TO_STDOUT", "false").lower() == "true"

# Limit for simultaneous transcription jobs
MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "2"))

# Backend options: 'thread' uses the internal queue, others may point to
# external systems like Celery.
JOB_QUEUE_BACKEND = os.getenv("JOB_QUEUE_BACKEND", "thread")

# Storage options: 'local' stores files on disk. Other backends can use cloud
# providers. Only 'local' is implemented here.
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")

# Authentication settings
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "admin")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    logging.critical("SECRET_KEY environment variable not set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
