#!/usr/bin/env python3
"""Validate that generated instruction files share the Blueprint bundle header."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLUEPRINT = ROOT / "docs" / "OPERATING_BLUEPRINT.md"
DEFAULT_TARGETS = [ROOT / "AGENTS.md", ROOT / "docs" / "CAG_instructions_master.md"]


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="*", type=Path, default=DEFAULT_TARGETS, help="files to check")
    parser.add_argument("--verbose", action="store_true", help="print compared values")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        b_id, b_utc = parse_header(BLUEPRINT)
        for target in args.targets:
            t_id, t_utc = parse_header(target)
            if args.verbose:
                print(f"{target}: Bundle-ID {t_id}, Bundle-UTC {t_utc}")
                print(f"Blueprint expects Bundle-ID {b_id}, Bundle-UTC {b_utc}")
            if t_id != b_id or t_utc != b_utc:
                print(f"Bundle mismatch in {target}", file=sys.stderr)
                return 1
        print("Bundle headers match.")
        return 0
    except Exception as exc:  # pragma: no cover - CLI path
        print(f"Error: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
