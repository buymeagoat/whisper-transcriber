#!/usr/bin/env python3

import os
import sys
import json
import shutil
import platform
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
EXCLUDED_DIRS = {"venv", "__pycache__"}
KEY_DIRS = ["uploads", "transcripts", "logs", "models"]
KEY_FILES = ["main.py", "metadata_writer.py", "models.py", ".env"]

def get_python_info():
    return {
        "version": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "architecture": platform.machine()
    }

def get_installed_packages():
    try:
        output = subprocess.check_output(["pip", "freeze"], text=True)
        return output.strip().splitlines()
    except Exception as e:
        return [f"ERROR: {e}"]

def list_project_files():
    structure = []
    for path in PROJECT_ROOT.rglob("*"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        rel_path = path.relative_to(PROJECT_ROOT)
        entry = {
            "type": "dir" if path.is_dir() else "file",
            "path": str(rel_path)
        }
        structure.append(entry)
    return structure

def load_env_file():
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return "Missing .env file"
    lines = [line.strip() for line in env_path.read_text().splitlines() if line.strip() and not line.startswith("#")]
    return lines

def check_cuda():
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return "torch not installed"

def get_whisper_bin():
    return shutil.which("whisper") or "Not found in PATH"

def read_critical_files():
    result = {}
    for name in KEY_FILES:
        f = PROJECT_ROOT / name
        if f.exists():
            result[name] = f.read_text()
        else:
            result[name] = "FILE NOT FOUND"
    return result

def main():
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "python_info": get_python_info(),
        "cuda_available": check_cuda(),
        "whisper_binary": get_whisper_bin(),
        "project_structure": list_project_files(),
        "installed_packages": get_installed_packages(),
        "env_file_contents": load_env_file(),
        "critical_file_contents": read_critical_files(),
    }

    out_path = PROJECT_ROOT / "environment_audit.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(f"✅ Environment audit written to: {out_path}")

if __name__ == "__main__":
    main()
