#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/full_test.log"

mkdir -p "$LOG_DIR"

{
    "$SCRIPT_DIR/run_tests.sh"
    npm test --prefix "$ROOT_DIR/frontend"
    npm run e2e --prefix "$ROOT_DIR/frontend"
} | tee "$LOG_FILE"

echo "Full test log saved to $LOG_FILE"
