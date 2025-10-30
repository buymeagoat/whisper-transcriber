#!/usr/bin/env bash
# Security: Enable strict error handling and security options
set -euo pipefail
IFS=$'\n\t'

# Security: Define secure logging and directory creation
LOG_FILE="/app/logs/entrypoint.log"
BUILD_INFO_FILE="/etc/whisper-build.info"

# Logging function for security audit trail
log_step() {
    echo "$(date -u +"%Y-%m-%d %H:%M:%S UTC") [ENTRYPOINT] $1"
}

require_secret() {
    local name="$1"
    local description="$2"
    local value="${!name-}"

    if [ -z "${value}" ]; then
        echo "ERROR: Required secret ${name} (${description}) is not set. Failing fast." >&2
        exit 1
    fi

    case "${value,,}" in
        "change-me"|"changeme"|"default"|"placeholder"|"example"|"sample"|"localtest")
            echo "ERROR: Required secret ${name} (${description}) is using an insecure placeholder value. Provide a rotated secret." >&2
            exit 1
            ;;
    esac
}

validate_required_secrets() {
    log_step "SECRETS"
    echo "Validating required runtime secrets (values redacted)" >&2

    require_secret "JWT_SECRET_KEY" "JWT signing key"
    require_secret "DATABASE_URL" "database connection string"
    require_secret "REDIS_URL" "Redis connection string"
    require_secret "ADMIN_BOOTSTRAP_PASSWORD" "bootstrap administrator password"

    log_step "SECRETS OK"
    echo "All required secrets are present" >&2
}

validate_build_metadata() {
    if [ ! -s "$BUILD_INFO_FILE" ]; then
        cat >&2 <<'EOM'
ERROR: Required Docker build metadata missing.
Rebuild the image with build arguments for BUILD_VERSION, BUILD_SHA, and BUILD_DATE.
EOM
        exit 1
    fi

    declare -A build_meta=()
    while IFS='=' read -r key value; do
        if [ -n "${key:-}" ]; then
            build_meta["$key"]="${value:-}"
        fi
    done < "$BUILD_INFO_FILE"

    local required_keys=(BUILD_VERSION BUILD_SHA BUILD_DATE)
    for key in "${required_keys[@]}"; do
        if [ -z "${build_meta[$key]:-}" ]; then
            echo "ERROR: Docker image missing $key metadata." >&2
            exit 1
        fi
    done

    if [ "${build_meta[BUILD_SHA]}" = "unknown" ] || [ "${build_meta[BUILD_DATE]}" = "unknown" ]; then
        local suggest_sha
        local suggest_date
        suggest_sha=$(git rev-parse HEAD 2>/dev/null || echo '<commit>')
        suggest_date=$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo '<timestamp>')
        log_step "BUILD WARNING"
        cat >&2 <<EOM
WARNING: Docker image built without full metadata.
Rebuild with:
  docker build \
    --build-arg BUILD_SHA=${suggest_sha} \
    --build-arg BUILD_DATE=${suggest_date} \
    --build-arg BUILD_VERSION=<version> \
    -t whisper-transcriber:latest .
EOM
    fi

    log_step "BUILD METADATA"
    echo "Using build metadata from $BUILD_INFO_FILE" >&2
    while IFS= read -r line; do
        echo "$line" >&2
    done < "$BUILD_INFO_FILE"
}

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

validate_build_metadata

log_step "ENVIRONMENT"
echo "Container entrypoint starting (environment variables redacted)" >&2

validate_required_secrets

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
