import os
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

# Raw environment variable for API host
RAW_VITE_API_HOST = os.getenv("VITE_API_HOST")
API_HOST = RAW_VITE_API_HOST or "http://localhost:8000"

DB_PATH = os.getenv("DB", "api/jobs.db")

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
LOG_TO_STDOUT = os.getenv("LOG_TO_STDOUT", "false").lower() == "true"

# Limit for simultaneous transcription jobs
MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "2"))

# Optional token required to access the /metrics endpoint
METRICS_TOKEN = os.getenv("METRICS_TOKEN")
