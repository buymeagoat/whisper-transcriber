#!/bin/sh
set -eu

if [ "${SERVICE_TYPE:-api}" = "worker" ]; then
    # succeed only if the Celery worker process is running
    pgrep -f "celery" >/dev/null || exit 1
else
    api_host="${VITE_API_HOST:-http://192.168.1.52:8000}"
    api_host="${api_host%/}"  # remove trailing slash if present
    curl -fs "$api_host/health" >/dev/null || exit 1
fi
