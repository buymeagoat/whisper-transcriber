#!/usr/bin/env python3
"""Capture repository snapshot metadata for Codex workflows."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

EXCLUDE_DIRS = {".git", "node_modules", ".venv"}


def run(cmd: list[str]) -> str | Dict:
    """Run command and return output or error string."""
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return out.strip()
    except Exception as exc:  # noqa: broad-except
        return f"error: {exc}"


def file_sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_tree(root: Path) -> Dict[str, str]:
    tree: Dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        parts = Path(dirpath).parts
        if any(part in EXCLUDE_DIRS for part in parts):
            dirnames[:] = []
            continue
        for name in list(dirnames):
            if name in EXCLUDE_DIRS:
                dirnames.remove(name)
        for fname in filenames:
            fp = Path(dirpath) / fname
            if any(part in EXCLUDE_DIRS for part in fp.parts):
                continue
            rel = fp.relative_to(root)
            tree[str(rel)] = file_sha1(fp)
    return tree


def pip_freeze() -> list[str] | str:
    out = run([sys.executable, "-m", "pip", "freeze"])
    return out.splitlines() if isinstance(out, str) else out


def npm_ls() -> Dict | str:
    result = run(["npm", "ls", "--depth=0", "--json"])
    return result


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    audit = {
        "commit": run(["git", "rev-parse", "HEAD"]),
        "timestamp": ts,
        "tree": collect_tree(root),
        "pip_freeze": pip_freeze(),
        "npm_ls": npm_ls(),
    }
    snap_dir = root / "snapshots"
    snap_dir.mkdir(exist_ok=True)
    snap_path = snap_dir / f"snapshot_{ts}.json"
    with open(snap_path, "w") as fh:
        json.dump(audit, fh, indent=2)
    sha256 = hashlib.sha256(snap_path.read_bytes()).hexdigest()
    print(f"{snap_path} {sha256}")


if __name__ == "__main__":
    main()
