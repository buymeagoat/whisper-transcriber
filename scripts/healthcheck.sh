#!/bin/sh
set -eu

if [ "${SERVICE_TYPE:-api}" = "worker" ]; then
    celery -A api.services.celery_app inspect ping -d "celery@$(hostname)" >/dev/null || exit 1
else
    curl -fs http://localhost:8000/health >/dev/null || exit 1
fi
