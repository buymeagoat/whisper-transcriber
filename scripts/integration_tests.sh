#!/usr/bin/env bash
set -euo pipefail

API_HOST="${VITE_API_HOST:-http://localhost:8000}"
API_HOST="${API_HOST%/}"

check_endpoint() {
    local path="$1"
    if curl -fsS "$API_HOST$path" >/dev/null; then
        echo "$path OK"
    else
        echo "$path FAILED"
        return 1
    fi
}

check_endpoint /health
check_endpoint /version

exit 0
