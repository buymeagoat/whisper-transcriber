#!/usr/bin/env bash
# Package the application as an RPM using fpm.
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION=$(grep -m1 version "$ROOT_DIR/pyproject.toml" | cut -d '"' -f2)
fpm -s python -t rpm -n whisper-transcriber -v "$VERSION" -p "$ROOT_DIR/dist" "$ROOT_DIR"
