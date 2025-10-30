#!/bin/sh
set -eu

if [ "${SERVICE_TYPE:-app}" = "worker" ]; then
    # succeed only if the Celery worker process is running
    pgrep -f "celery" >/dev/null || exit 1
else
    api_host="${VITE_API_HOST:-http://localhost:8001}"
    api_host="${api_host%/}"  # remove trailing slash if present
    curl -fsS "$api_host/livez" >/dev/null || exit 1
    curl -fsS "$api_host/readyz" >/dev/null || exit 1
fi
