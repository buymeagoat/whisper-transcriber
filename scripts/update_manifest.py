#!/usr/bin/env python3
"""
Script to generate/update local_manifest.txt with a list of all files in the repository (excluding .git, venv, node_modules, and transient log files).
"""
import os

EXCLUDE_DIRS = {'.git', 'venv', 'node_modules', 'logs/app', 'logs/**/raw'}
EXCLUDE_FILES = {'*.log', '*.tmp'}
MANIFEST_PATH = os.path.join('cache', 'manifest.txt')


def should_exclude(path):
    for ex in EXCLUDE_DIRS:
        if ex.endswith('/**/raw'):
            if '/raw/' in path:
                return True
        elif ex in path:
            return True
    for ex in EXCLUDE_FILES:
        if path.endswith(ex[1:]):
            return True
    return False

def collect_files(root):
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Exclude directories
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == '.':
            rel_dir = ''
        skip = False
        for ex in EXCLUDE_DIRS:
            if ex in rel_dir:
                skip = True
                break
        if skip:
            continue
        for fname in filenames:
            rel_path = os.path.join(rel_dir, fname) if rel_dir else fname
            if not should_exclude(rel_path):
                files.append(rel_path)
    return sorted(files)

def main():
    files = collect_files('.')
    with open(MANIFEST_PATH, 'w') as f:
        for file in files:
            f.write(file + '\n')
    from datetime import datetime
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Manifest updated: {MANIFEST_PATH} ({len(files)} files)")

if __name__ == '__main__':
    main()