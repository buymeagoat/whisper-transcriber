#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/shared_checks.sh"

# Initialize CACHE_DIR and capture any warning output
warn_file=$(mktemp)
set_cache_dir 2>"$warn_file"
warning=$(cat "$warn_file")
rm -f "$warn_file"

# Determine environment type
if grep -qi microsoft /proc/version; then
    env_type="WSL"
else
    env_type="Linux"
fi

[ -n "${CI:-}" ] && env_type="$env_type (CI)"

cat <<INFO
Environment: $env_type
CACHE_DIR: $CACHE_DIR
INFO

if [ "${CACHE_OVERRIDE_WARNING:-0}" -eq 1 ]; then
    echo "Override warning triggered"
    echo "$warning"
else
    echo "Override warning not triggered"
fi
