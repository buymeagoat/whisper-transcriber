#!/usr/bin/env python3
"""Validate that generated instruction files share the Blueprint bundle header."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLUEPRINT = ROOT / "docs" / "OPERATING_BLUEPRINT.md"
AGENTS = ROOT / "AGENTS.md"
CAG_MASTER = ROOT / "docs" / "CAG_instructions_master.md"

def parse_header(path: Path) -> tuple[str, str]:
    bundle_id = bundle_utc = None
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("Bundle-ID:"):
                bundle_id = line.split(":", 1)[1].strip()
            elif line.startswith("Bundle-UTC:"):
                bundle_utc = line.split(":", 1)[1].strip()
            if bundle_id and bundle_utc:
                break
    if bundle_id is None or bundle_utc is None:
        raise ValueError(f"Missing bundle header in {path}")
    return bundle_id, bundle_utc

def main() -> int:
    b_id, b_utc = parse_header(BLUEPRINT)
    for target in (AGENTS, CAG_MASTER):
        t_id, t_utc = parse_header(target)
        if t_id != b_id or t_utc != b_utc:
            print(f"Bundle mismatch in {target}")
            return 1
    print("Bundle headers match.")
    return 0

if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
