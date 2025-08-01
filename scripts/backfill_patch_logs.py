#!/usr/bin/env python3
"""Generate patch logs for commits that lack them."""
from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PATCH_LOG_DIR = Path("docs/patch_logs")
TEMPLATE = f"""patch_{{timestamp}}_{{commit}}.log
=====TASK=====
Backfill legacy patch log

=====OBJECTIVE=====
Record missing patch log from history

=====CONSTRAINTS=====
- Snapshot metadata unavailable
- Test results unavailable

=====SCOPE=====
LEGACY-N/A

=====DIFFSUMMARY=====
{{summary}}

=====TIMESTAMP=====
{{commit_iso}}

=====BUILDER_DATE_TIME (UTC)=====
LEGACY-N/A

=====PROMPTID=====
backfill-patch-logs

=====AGENTVERSION=====
LEGACY-N/A

=====AGENTHASH=====
LEGACY-N/A

=====PROMPTHASH=====
LEGACY-N/A

=====COMMITHASH=====
{{full_hash}}

=====SPEC_HASHES=====
LEGACY-N/A

=====SNAPSHOT=====
LEGACY-N/A

=====TESTRESULTS=====
LEGACY-N/A

=====DIAGNOSTICMETA=====
LEGACY-N/A

=====DECISIONS=====
- Generated automatically by backfill_patch_logs.py
"""

def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()

def existing_commit_hashes() -> set[str]:
    hashes = set()
    pattern = re.compile(r"^=====COMMITHASH=====\n(.+)", re.MULTILINE)
    for path in PATCH_LOG_DIR.glob("patch_*.log"):
        try:
            text = path.read_text()
        except Exception:
            continue
        m = pattern.search(text)
        if m:
            h = m.group(1).strip()
            if h and not h.startswith("LEGACY") and h != "TBD":
                hashes.add(h)
    return hashes

def commit_history() -> list[tuple[str,str,str]]:
    log_format = "%H|%cI|%s"
    out = run(["git", "log", "--reverse", "--pretty=format:%s" % log_format])
    commits = []
    for line in out.splitlines():
        h, iso, msg = line.split("|", 2)
        commits.append((h, iso, msg))
    return commits

def sanitize_summary(msg: str) -> str:
    return msg.strip().replace("\n", " ")

def main() -> None:
    PATCH_LOG_DIR.mkdir(parents=True, exist_ok=True)
    existing = existing_commit_hashes()
    for commit, iso, msg in commit_history():
        if commit in existing:
            continue
        dt = datetime.fromisoformat(iso).astimezone(timezone.utc)
        timestamp = dt.strftime("%Y%m%d_%H%M%S")
        filename = PATCH_LOG_DIR / f"patch_{timestamp}_{commit[:7]}.log"
        if filename.exists():
            continue
        content = TEMPLATE.format(
            timestamp=timestamp,
            commit=commit[:7],
            summary=sanitize_summary(msg) or "LEGACY-N/A",
            commit_iso=dt.isoformat().replace("+00:00", "Z"),
            full_hash=commit,
        )
        filename.write_text(content)
        print(f"Generated {filename}")

if __name__ == "__main__":
    main()
