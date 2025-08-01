import json
import os
import subprocess
from pathlib import Path

def test_audit_snapshot(tmp_path):
    script = Path(__file__).resolve().parents[1] / 'CPG_repo_audit.py'
    result = subprocess.check_output([script], text=True)
    path_str = result.strip().split()[0]
    snap_path = Path(path_str)
    assert snap_path.exists(), f"snapshot not found: {snap_path}"
    data = json.loads(snap_path.read_text())
    for key in ["commit", "timestamp", "tree", "pip_freeze", "npm_ls"]:
        assert key in data
    os.remove(snap_path)
