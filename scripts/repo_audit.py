# /scripts/repo_audit.py

import os
import hashlib
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, '..'))
OUTPUT_FILE = os.path.join(PROJECT_ROOT, 'logs', 'repo_audit.md')

EXCLUDE_DIRS = {
    '.git', '__pycache__', '.pytest_cache', '.venv', 'venv',
    'node_modules', 'cache', 'frontend/dist', '.mypy_cache'
}
EXCLUDE_EXTENSIONS = {
    '.deb', '.png', '.svg', '.pyc', '.log', '.zip'
}
EXCLUDE_FILENAMES = {'.env', '.env.example'}
MAX_FILE_SIZE_BYTES = 1_000_000  # 1 MB limit for inclusion

def should_exclude(path, size):
    if any(part in EXCLUDE_DIRS for part in path.split(os.sep)):
        return True
    if os.path.basename(path) in EXCLUDE_FILENAMES:
        return True
    if os.path.splitext(path)[1].lower() in EXCLUDE_EXTENSIONS:
        return True
    if size > MAX_FILE_SIZE_BYTES:
        return True
    return False

def sha256sum(file_path):
    h = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"

def scan_repo(root):
    entries = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fname in filenames:
            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, start=root)
            try:
                size = os.path.getsize(full_path)
                if should_exclude(rel_path, size):
                    continue
                mtime = os.path.getmtime(full_path)
                mtime_str = datetime.utcfromtimestamp(mtime).isoformat()
                sha = sha256sum(full_path)
                entries.append((rel_path, size, mtime_str, sha))
            except Exception as e:
                entries.append((rel_path, 'ERROR', 'ERROR', str(e)))
    return entries

def write_audit(entries):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('# Filtered Repository Audit\n\n')
        f.write('| Path | Size (bytes) | Modified (UTC) | SHA-256 |\n')
        f.write('|------|---------------|----------------|---------|\n')
        for path, size, mtime, sha in sorted(entries):
            f.write(f'| {path} | {size} | {mtime} | {sha} |\n')

if __name__ == '__main__':
    audit_data = scan_repo(PROJECT_ROOT)
    write_audit(audit_data)
    print(f"Filtered audit written to {OUTPUT_FILE}")
