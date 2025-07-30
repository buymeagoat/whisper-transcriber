"""
dual_repo_audit.py

This script performs a full and filtered audit of the local Git repository.

Outputs:
- logs/repo_audit_full.md:    A complete scan of all files (no filters)
- logs/repo_audit_filtered.md: A filtered scan excluding volatile, large, or irrelevant files

Purpose:
- Establishes a deterministic view of repository contents for Codex Analyst GPT (CPG)
- Enables differential analysis between what Codex sees (filtered) and what exists (full)
- Serves as the foundation for verifying Codex patch accuracy and hallucination prevention

Filtering Logic:
- Excludes common build/output/virtualenv dirs (e.g., __pycache__, .venv, node_modules)
- Skips large files (>5MB) and irrelevant extensions (.zip, .pyc, .svg, etc.)
- Excludes sensitive or noisy filenames like `.env`
- Respects core directories (e.g., logs/, cache/, models/) now explicitly retained

Usage:
  Run from the project root:
      python scripts/dual_repo_audit.py

Maintainer:
  Codex Process Governance
"""


import os
import hashlib
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, '..'))
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
FULL_AUDIT = os.path.join(LOG_DIR, 'repo_audit_full.md')
FILTERED_AUDIT = os.path.join(LOG_DIR, 'repo_audit_filtered.md')

EXCLUDE_DIRS = {
    '.git', '__pycache__', '.pytest_cache', '.venv', 'venv',
    'node_modules', 'frontend/dist', '.mypy_cache'
}
EXCLUDE_EXTENSIONS = {
    '.deb', '.pyc', '.zip', '.svg', '.png'
}
EXCLUDE_FILENAMES = {'.env', '.env.example'}
MAX_FILE_SIZE_BYTES = 5_000_000  # relaxed to 5MB

def sha256sum(file_path):
    h = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"

def scan_repo(root, filtered=False):
    entries = []
    for dirpath, dirnames, filenames in os.walk(root):
        if filtered:
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fname in filenames:
            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, start=root)
            try:
                size = os.path.getsize(full_path)
                if filtered:
                    if any(part in EXCLUDE_DIRS for part in rel_path.split(os.sep)):
                        continue
                    if os.path.basename(rel_path) in EXCLUDE_FILENAMES:
                        continue
                    if os.path.splitext(rel_path)[1].lower() in EXCLUDE_EXTENSIONS:
                        continue
                    if size > MAX_FILE_SIZE_BYTES:
                        continue
                mtime = os.path.getmtime(full_path)
                mtime_str = datetime.utcfromtimestamp(mtime).isoformat()
                sha = sha256sum(full_path)
                entries.append((rel_path, size, mtime_str, sha))
            except Exception as e:
                entries.append((rel_path, 'ERROR', 'ERROR', str(e)))
    return entries

def write_audit(entries, filepath, title):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f'# {title}\n\n')
        f.write('| Path | Size (bytes) | Modified (UTC) | SHA-256 |\n')
        f.write('|------|---------------|----------------|---------|\n')
        for path, size, mtime, sha in sorted(entries):
            f.write(f'| {path} | {size} | {mtime} | {sha} |\n')

if __name__ == '__main__':
    full = scan_repo(PROJECT_ROOT, filtered=False)
    filtered = scan_repo(PROJECT_ROOT, filtered=True)
    write_audit(full, FULL_AUDIT, "Full Repository Audit")
    write_audit(filtered, FILTERED_AUDIT, "Filtered Repository Audit")
    print("✅ Audits written to:")
    print(f"  {FULL_AUDIT}")
    print(f"  {FILTERED_AUDIT}")
