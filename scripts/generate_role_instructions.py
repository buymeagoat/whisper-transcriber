#!/usr/bin/env python3
"""Generate CAG and Codex role instruction documents from the Blueprint.

Reads the bundle header from ``docs/OPERATING_BLUEPRINT.md`` and renders the
templates in ``docs/templates`` using simple string replacement. The resulting
documents are written to ``docs/CAG_instructions_master.md`` and ``AGENTS.md``
with a shared bundle header banner.

The script offers three flags:

``--check``
    Parse the Blueprint header, verify templates exist, and exit without
    writing any files.

``--dry-run``
    Render CAG instructions followed by AGENTS instructions to ``stdout`` with
    a separator. No files are written.

``--outdir PATH``
    Write output files to ``PATH`` instead of the repository default.

This script uses only the Python standard library and is idempotent: running it
multiple times with unchanged inputs produces identical outputs.
"""
from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLUEPRINT_PATH = ROOT / "docs" / "OPERATING_BLUEPRINT.md"
TEMPLATE_DIR = ROOT / "docs" / "templates"
OUTPUT_CAG = ROOT / "docs" / "CAG_instructions_master.md"
OUTPUT_AGENTS = ROOT / "AGENTS.md"

def parse_bundle_header(path: Path) -> dict:
    """Extract and validate bundle header fields from the Blueprint."""
    fields = {
        "BUNDLE_ID": None,
        "BUNDLE_UTC": None,
        "BLUEPRINT_VERSION": None,
        "SOURCE_OF_TRUTH": None,
    }
    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                lower = line.lower()
                for key in list(fields):
                    token = key.replace("_", "-").lower() + ":"
                    if lower.startswith(token):
                        fields[key] = line.split(":", 1)[1].strip()
                if all(fields.values()):
                    break
    except FileNotFoundError:
        raise FileNotFoundError(f"Blueprint not found at {path}")

    missing = [k for k, v in fields.items() if v is None]
    if missing:
        raise ValueError(f"Missing bundle header field(s) in Blueprint: {', '.join(missing)}")

    if not re.fullmatch(r"\d{8}", fields["BUNDLE_UTC"]):
        raise ValueError("Bundle-UTC must match ^\\d{8}$ (YYYYMMDD)")
    try:
        if int(fields["BUNDLE_ID"]) <= 0:
            raise ValueError
    except ValueError:
        raise ValueError("Bundle-ID must be a positive integer")

    return fields

def render_template(template_path: Path, context: dict) -> str:
    try:
        text = template_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:  # pragma: no cover - defensive
        raise FileNotFoundError(f"Missing template: {template_path}") from exc
    for key, value in context.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text

def build_header(context: dict, generated_at: str) -> str:
    return (
        "<!-- Auto-generated from OPERATING_BLUEPRINT.md; do not edit directly. -->\n"
        f"Bundle-ID: {context['BUNDLE_ID']}\n"
        f"Bundle-UTC: {context['BUNDLE_UTC']}\n"
        f"Blueprint-Version: {context['BLUEPRINT_VERSION']}\n"
        f"Source-of-Truth: {context['SOURCE_OF_TRUTH']}\n"
        f"Generated-At: {generated_at}\n\n"
    )


def write_file(path: Path, content: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip("\n") + "\n", encoding="utf-8")
    except PermissionError as exc:  # pragma: no cover - environmental
        raise PermissionError(f"Cannot write to {path}: {exc}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="validate inputs without writing")
    group.add_argument("--dry-run", action="store_true", help="print rendered outputs to stdout")
    parser.add_argument("--outdir", type=Path, default=None, help="output directory for generated files")
    return parser.parse_args()

def main() -> int:
    args = parse_args()
    try:
        bundle = parse_bundle_header(BLUEPRINT_PATH)
        generated_at = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        context = {**bundle, "GENERATED_AT": generated_at}

        # Ensure templates exist
        tpl_cag = TEMPLATE_DIR / "CAG_instructions.human.md.tpl"
        tpl_agents = TEMPLATE_DIR / "AGENTS.human.md.tpl"
        if not tpl_cag.is_file() or not tpl_agents.is_file():
            missing = [p for p in (tpl_cag, tpl_agents) if not p.is_file()]
            raise FileNotFoundError(f"Missing template(s): {', '.join(str(p) for p in missing)}")

        if args.check:
            print("Blueprint header and templates validated.")
            return 0

        cag_body = render_template(tpl_cag, context)
        agents_body = render_template(tpl_agents, context)
        header = build_header(bundle, generated_at)

        if args.dry_run:
            print("=== CAG_instructions_master.md ===")
            print(header + cag_body)
            print("=== AGENTS.md ===")
            print(header + agents_body)
            return 0

        outdir = args.outdir if args.outdir else None
        cag_path = OUTPUT_CAG if outdir is None else Path(outdir) / "CAG_instructions_master.md"
        agents_path = OUTPUT_AGENTS if outdir is None else Path(outdir) / "AGENTS.md"

        write_file(cag_path, header + cag_body)
        write_file(agents_path, header + agents_body)
        print(f"Generated CAG and AGENTS instruction drafts at {cag_path.parent} and {agents_path.parent}.")
        return 0
    except Exception as exc:  # pragma: no cover - CLI path
        print(f"Error: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
