"""Entry point for launching the Celery worker."""

import os
import sys

if __name__ == "__main__":
    # Use celery CLI directly
    os.execvp('celery', ['celery', '-A', 'api.services.celery_app', 'worker', '--loglevel=info'])
