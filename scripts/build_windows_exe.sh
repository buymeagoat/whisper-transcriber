#!/usr/bin/env bash
# Build a standalone Windows executable using PyInstaller.
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
pyinstaller --onefile --name whisper-transcriber "$SCRIPT_DIR/server_entry.py" --distpath "$ROOT_DIR/dist"
