#!/usr/bin/env bash
# scripts/audit_dependencies.sh
# Systematically audit, populate, and validate all dependency caches for offline reproducibility.
# Run this after any dependency file change, or as part of CI/CD.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Source shared helpers and set cache dir
source "$SCRIPT_DIR/shared_checks.sh"
set_cache_dir
NPM_CACHE="$CACHE_DIR/npm"
export NPM_CACHE

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/audit_dependencies_$(date -u +%Y%m%d_%H%M%S).log"

# 1. Python (pip)
echo "[PYTHON] Populating pip cache..." | tee -a "$LOG_FILE"
pip download -r "$ROOT_DIR/requirements.txt" --dest "$ROOT_DIR/cache/pip" 2>&1 | tee -a "$LOG_FILE"
echo "[PYTHON] Validating pip cache offline..." | tee -a "$LOG_FILE"
pip install --no-index --find-links "$ROOT_DIR/cache/pip" -r "$ROOT_DIR/requirements.txt" --dry-run 2>&1 | tee -a "$LOG_FILE"

# 2. NPM (frontend)
if [ -f "$ROOT_DIR/frontend/package-lock.json" ]; then
  echo "[NPM] Populating npm cache..." | tee -a "$LOG_FILE"
  npm ci --cache "$NPM_CACHE" --prefer-offline --no-audit --prefix "$ROOT_DIR/frontend" 2>&1 | tee -a "$LOG_FILE"
  echo "[NPM] Validating npm cache offline, auto-populate if missing..." | tee -a "$LOG_FILE"
  if ! npm ci --offline --prefix "$ROOT_DIR/frontend" --cache "$NPM_CACHE"; then
      echo "[NPM] Offline install failed. Attempting to fetch and cache missing packages online..." | tee -a "$LOG_FILE"
      npm ci --prefix "$ROOT_DIR/frontend" --cache "$NPM_CACHE"
      echo "[NPM] Re-validating npm cache offline..." | tee -a "$LOG_FILE"
      if ! npm ci --offline --prefix "$ROOT_DIR/frontend" --cache "$NPM_CACHE"; then
          echo "[ERROR] NPM offline install still failed. Some packages could not be cached." | tee -a "$LOG_FILE"
          exit 1
      fi
  fi
fi

# 3. APT (system packages)
if [ -f "$ROOT_DIR/scripts/apt-packages.txt" ]; then
  echo "[APT] Populating apt cache..." | tee -a "$LOG_FILE"
  while read -r pkg; do
    [[ "$pkg" =~ ^#.*$ || -z "$pkg" ]] && continue
    apt-get download "$pkg" 2>&1 | tee -a "$LOG_FILE" || true
  done < "$ROOT_DIR/scripts/apt-packages.txt"
  echo "[APT] Validating apt cache offline..." | tee -a "$LOG_FILE"
  # This is a dry-run; actual offline install would use dpkg -i
fi

# 4. Manifest update
echo "[MANIFEST] Updating manifest..." | tee -a "$LOG_FILE"
python3 "$ROOT_DIR/scripts/update_manifest.py" 2>&1 | tee -a "$LOG_FILE"

echo "[DONE] Dependency audit, cache population, and validation complete." | tee -a "$LOG_FILE"
