#!/usr/bin/env bash
# Security: Enable strict error handling and security options
set -euo pipefail
IFS=$'\n\t'

# Security: Define secure logging and directory creation
LOG_FILE="/app/logs/entrypoint.log"
BUILD_INFO_FILE="/etc/whisper-build.info"
BROKER_DEFAULT_TIMEOUT=60

PLACEHOLDER_SENTINELS=(change-me changeme default placeholder example sample localtest)

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

    local lowered="${value,,}"
    for placeholder in "${PLACEHOLDER_SENTINELS[@]}"; do
        if [ "$lowered" = "$placeholder" ]; then
            echo "ERROR: Required secret ${name} (${description}) is using an insecure placeholder value. Provide a rotated secret." >&2
            exit 1
        fi
    done
}

validate_required_secrets() {
    log_step "SECRETS"
    echo "Validating required runtime secrets (values redacted)" >&2

    require_secret "SECRET_KEY" "application signing key"
    require_secret "JWT_SECRET_KEY" "JWT signing key"
    require_secret "DATABASE_URL" "database connection string"
    require_secret "REDIS_URL" "Redis connection string"
    require_secret "ADMIN_BOOTSTRAP_PASSWORD" "bootstrap administrator password"
    require_secret "REDIS_PASSWORD" "Redis password"

    log_step "SECRETS OK"
    echo "All required secrets are present" >&2
}

ensure_non_root() {
    if [ "$(id -u)" -eq 0 ]; then
        echo "WARNING: Running as root - this should only happen during initialization" >&2
        if command -v gosu >/dev/null 2>&1; then
            chown -R appuser:appuser /app/storage /app/logs /app/data 2>/dev/null || true
            exec gosu appuser "$0" "$@"
        else
            echo "ERROR: gosu is required to drop root privileges but is not installed" >&2
            exit 1
        fi
    fi

    if [ "$(id -u)" -ne 1000 ] || [ "$(id -g)" -ne 1000 ]; then
        echo "ERROR: Container must run as user appuser (uid=1000, gid=1000)" >&2
        echo "Current: uid=$(id -u), gid=$(id -g), user=$(whoami)" >&2
        exit 1
    fi
}

check_database_connectivity() {
    log_step "DATABASE"
    python - <<'PY'
import os
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


def main() -> None:
    url = os.environ["DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True, future=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        print(f"Database connectivity check failed: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - defensive fallback
        print(f"Unexpected error while checking database connectivity: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
PY
    log_step "DATABASE OK"
}

check_broker_connectivity() {
    local broker_url="${CELERY_BROKER_URL:-${REDIS_URL}}"
    local result_url="${CELERY_RESULT_BACKEND:-$broker_url}"
    local max_wait="${BROKER_PING_TIMEOUT:-$BROKER_DEFAULT_TIMEOUT}"

    log_step "BROKER"
    BROKER_URL="$broker_url" RESULT_URL="$result_url" TIMEOUT="$max_wait" \
    python - <<'PY'
import os
import sys
import time
from urllib.parse import urlparse

try:
    from redis import Redis
except ImportError as exc:  # pragma: no cover - runtime safety
    print(f"redis library missing: {exc}", file=sys.stderr)
    sys.exit(1)


def build_params(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in {"redis", "rediss"}:
        raise ValueError(f"Unsupported Redis scheme: {parsed.scheme}")
    return {
        "host": parsed.hostname or "redis",
        "port": parsed.port or 6379,
        "db": int(parsed.path.lstrip("/") or 0),
        "username": parsed.username,
        "password": parsed.password,
        "ssl": parsed.scheme == "rediss",
        "socket_connect_timeout": 5,
    }


def wait_for(url: str, timeout: int) -> None:
    deadline = time.monotonic() + timeout
    attempt = 0
    params = build_params(url)
    last_error = None

    while time.monotonic() < deadline:
        attempt += 1
        try:
            client = Redis(**params)
            client.ping()
            client.close()
            print(f"Redis ready at {url} (attempt {attempt})")
            return
        except Exception as exc:  # pragma: no cover - network dependent
            last_error = exc
            sleep_for = min(2 ** (attempt - 1), 5)
            print(
                f"Redis not ready at {url} (attempt {attempt}): {exc}. Retrying in {sleep_for}s",
                file=sys.stderr,
            )
            time.sleep(sleep_for)

    raise RuntimeError(f"Redis not ready after {timeout}s: {last_error}")


timeout = int(os.environ["TIMEOUT"])
wait_for(os.environ["BROKER_URL"], timeout)
result_url = os.environ.get("RESULT_URL")
if result_url and result_url != os.environ["BROKER_URL"]:
    wait_for(result_url, timeout)
PY
    log_step "BROKER OK"
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
mkdir -p /app/data /app/storage/uploads /app/storage/transcripts /app/logs /app/models
chown -R appuser:appuser /app/data /app/storage /app/logs /app/models 2>/dev/null || true

ensure_non_root "$@"

# Security: Set up secure logging with log rotation consideration
exec > >(tee -a "$LOG_FILE") 2>&1

validate_build_metadata

log_step "ENVIRONMENT"
echo "Container entrypoint starting (environment variables redacted)" >&2

validate_required_secrets

check_database_connectivity
check_broker_connectivity

if [ "${SERVICE_TYPE:-app}" = "worker" ] && [ ! -f /app/api/worker.py ]; then
    echo "ERROR: /app/api/worker.py not found" >&2
    exit 1
fi
log_step "START"
echo "Executing: $@" >&2
# If we're already running as appuser (from Docker user setting), execute directly
if [ "$(id -u)" -eq 1000 ]; then
    exec "$@"
else
    exec gosu appuser "$@"
fi
