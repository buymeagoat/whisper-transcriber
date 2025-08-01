#!/usr/bin/env python3
"""Collect basic repository metadata for Codex patch logging.

Outputs JSON with commit hash, UTC timestamp, a simple directory
summary, parsed dependency versions and discovered tests.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def run(cmd: List[str]) -> str:
    """Return command output or error string."""
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:  # noqa: broad-except
        return f"error: {exc}"


def get_commit_hash() -> str:
    return run(["git", "rev-parse", "HEAD"])


def get_utc_timestamp() -> str:
    return datetime.utcnow().isoformat() + "Z"


def directory_tree_summary(root: Path) -> Dict[str, Any]:
    summary: Dict[str, Any] = {"total_files": 0, "dirs": {}}
    for path, _, files in os.walk(root):
        if ".git" in path.split(os.sep):
            continue
        rel = os.path.relpath(path, root)
        summary["dirs"][rel] = len(files)
        summary["total_files"] += len(files)
    return summary


def parse_requirements() -> Dict[str, str]:
    deps: Dict[str, str] = {}
    for req in ["requirements.txt", "requirements-dev.txt"]:
        if not os.path.exists(req):
            continue
        with open(req) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                if "==" in line:
                    name, ver = line.split("==", 1)
                else:
                    name, ver = line, ""
                deps[name] = ver
    return deps


def collect_tests() -> List[str] | str:
    try:
        out = subprocess.check_output(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            text=True,
            stderr=subprocess.STDOUT,
        )
        return [line.strip() for line in out.splitlines() if line.strip()]
    except Exception as exc:  # noqa: broad-except
        return f"error: {exc}"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    audit = {
        "commit": get_commit_hash(),
        "timestamp": get_utc_timestamp(),
        "tree": directory_tree_summary(root),
        "dependencies": parse_requirements(),
        "tests": collect_tests(),
    }
    json.dump(audit, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
