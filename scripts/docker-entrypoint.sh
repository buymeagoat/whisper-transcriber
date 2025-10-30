#!/usr/bin/env bash
# Security: Enable strict error handling and security options
set -euo pipefail
IFS=$'\n\t'

# Security: Define secure logging and directory creation
LOG_FILE="/app/logs/entrypoint.log"

# Security: Create required directories with proper permissions (non-root safe)
mkdir -p /app/storage/uploads /app/storage/transcripts /app/logs /app/data

# Security: Only set ownership if running as root (for initialization)
if [ "$(id -u)" -eq 0 ]; then
    echo "WARNING: Running as root - this should only happen during initialization"
    chown -R appuser:appuser /app/storage /app/logs /app/data
    # Security: Drop privileges using gosu
    exec gosu appuser "$0" "$@"
fi

# Security: Verify we're running as the correct user
if [ "$(id -u)" -ne 1000 ] || [ "$(id -g)" -ne 1000 ]; then
    echo "ERROR: Container must run as user appuser (uid=1000, gid=1000)" >&2
    echo "Current: uid=$(id -u), gid=$(id -g), user=$(whoami)" >&2
    exit 1
fi

# Security: Set up secure logging with log rotation consideration
exec > >(tee -a "$LOG_FILE") 2>&1

# Logging function for security audit trail
log_step() {
    echo "$(date -u +"%Y-%m-%d %H:%M:%S UTC") [ENTRYPOINT] $1"
}

log_step "ENVIRONMENT"
echo "Container entrypoint starting (environment variables redacted)" >&2

# If this container is running a worker, wait for the broker to be ready
if [ "${SERVICE_TYPE:-app}" = "worker" ]; then
    if [ ! -f /app/api/worker.py ]; then
        echo "ERROR: /app/api/worker.py not found" >&2
        exit 1
    fi
    broker_url="${REDIS_URL:-redis://redis:6379/0}"
    max_wait=${BROKER_PING_TIMEOUT:-60}
    log_step "WAIT FOR BROKER"
    BROKER_URL="$broker_url" TIMEOUT="$max_wait" \
    python - <<'PY'
import os
import socket
import sys
import time
from urllib.parse import urlparse

url = urlparse(os.environ["BROKER_URL"])
host = url.hostname or "redis"
port = url.port or 6379
timeout = int(os.environ["TIMEOUT"])
start = time.time()

while True:
    try:
        with socket.create_connection((host, port), timeout=1):
            break
    except OSError:
        if time.time() - start >= timeout:
            print(f"Broker unreachable after {timeout}s", file=sys.stderr)
            sys.exit(1)
        time.sleep(1)
PY
fi
log_step "START"
echo "Executing: $@" >&2
# If we're already running as appuser (from Docker user setting), execute directly
if [ "$(id -u)" -eq 1000 ]; then
    exec "$@"
else
    exec gosu appuser "$@"
fi
