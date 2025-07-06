#!/bin/sh
set -eu

if [ "${SERVICE_TYPE:-api}" = "worker" ]; then
    # succeed only if the Celery worker process is running
    pgrep -f "celery" >/dev/null || exit 1
else
    curl -fs http://localhost:8000/health >/dev/null || exit 1
fi
