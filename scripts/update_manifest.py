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
    import subprocess
    from datetime import datetime
    files = collect_files('.')
    # Gather required metadata
    # BASE_CODENAME from Dockerfile base image
    base_image = None
    base_codename = None
    base_digest = None
    dockerfile_path = 'Dockerfile'
    try:
        with open(dockerfile_path) as df:
            for line in df:
                if line.startswith('FROM '):
                    base_image = line.split()[1].strip()
                    break
        if base_image:
            # Get codename from base image
            result = subprocess.run([
                'docker', 'run', '--rm', base_image,
                'bash', '-c', 'source /etc/os-release && echo $VERSION_CODENAME'
            ], capture_output=True, text=True)
            base_codename = result.stdout.strip() if result.returncode == 0 else ''
            # Get digest from base image
            result = subprocess.run([
                'docker', 'image', 'inspect', base_image,
                '--format', '{{index .RepoDigests 0}}'
            ], capture_output=True, text=True)
            if result.returncode == 0 and '@' in result.stdout:
                base_digest = result.stdout.strip().split('@')[1]
            else:
                base_digest = ''
    except Exception:
        base_codename = ''
        base_digest = ''
    # TIMESTAMP
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Generate pip_versions.txt for later cache validation
    pip_versions = ''
    pip_versions_path = os.path.join('cache', 'pip', 'pip_versions.txt')
    try:
        os.makedirs(os.path.dirname(pip_versions_path), exist_ok=True)
        result = subprocess.run(
            ['pip', 'list', '--format=freeze'],
            check=True,
            capture_output=True,
            text=True,
        )
        with open(pip_versions_path, 'w') as pf:
            pf.write(result.stdout)
    except Exception:
        pass
    if os.path.exists(pip_versions_path):
        try:
            import hashlib
            with open(pip_versions_path, 'rb') as pf:
                pip_versions = hashlib.sha256(pf.read()).hexdigest()
        except Exception:
            pip_versions = ''
    # npm_versions
    npm_versions = ''
    npm_versions_path = 'cache/npm/npm_versions.txt'
    if os.path.exists(npm_versions_path):
        try:
            import hashlib
            with open(npm_versions_path, 'rb') as nf:
                npm_versions = hashlib.sha256(nf.read()).hexdigest()
        except Exception:
            npm_versions = ''
    with open(MANIFEST_PATH, 'w') as f:
        f.write(f"BASE_CODENAME={base_codename}\n")
        f.write(f"BASE_DIGEST={base_digest}\n")
        f.write(f"TIMESTAMP={timestamp}\n")
        f.write(f"pip_versions={pip_versions}\n")
        f.write(f"npm_versions={npm_versions}\n")
        f.write("\n")
        for file in files:
            f.write(file + '\n')
    print(f"[{timestamp}] Manifest updated: {MANIFEST_PATH} ({len(files)} files)")

if __name__ == '__main__':
    main()
