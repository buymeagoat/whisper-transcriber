"""
Celery worker for background transcription processing
Integrates with the API application for job processing
"""

import os
import sys
from pathlib import Path
from celery import Celery

# Ensure we can import from api package
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.settings import settings

# Setup Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery setup
celery_app = Celery("whisper_transcriber", broker=REDIS_URL, backend=REDIS_URL)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
)

# Auto-discover tasks from api.services
celery_app.autodiscover_tasks(['api.services'])

if __name__ == '__main__':
    celery_app.start()