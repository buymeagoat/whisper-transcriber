#!/usr/bin/env python3
"""Generate CAG and Codex role instruction documents from the Blueprint.

Reads the bundle header from ``docs/OPERATING_BLUEPRINT.md`` and renders
``/docs/templates/CAG_instructions.human.md.tpl`` and
``/docs/templates/AGENTS.human.md.tpl`` using simple string replacement.
The resulting documents are written to ``/docs/CAG_instructions_master.md``
and ``/AGENTS.md`` respectively with a shared bundle header banner.

This script uses only the Python standard library and is idempotent: running it
multiple times with unchanged inputs produces identical outputs.
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLUEPRINT_PATH = ROOT / "docs" / "OPERATING_BLUEPRINT.md"
TEMPLATE_DIR = ROOT / "docs" / "templates"
OUTPUT_CAG = ROOT / "docs" / "CAG_instructions_master.md"
OUTPUT_AGENTS = ROOT / "AGENTS.md"

def parse_bundle_header(path: Path) -> dict:
    """Extract bundle header fields from the Blueprint."""
    fields = {
        "BUNDLE_ID": None,
        "BUNDLE_UTC": None,
        "BLUEPRINT_VERSION": None,
        "SOURCE_OF_TRUTH": None,
    }
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            lower = line.lower()
            for key in list(fields):
                token = key.replace("_", "-").lower() + ":"
                if lower.startswith(token):
                    fields[key] = line.split(":", 1)[1].strip()
            if all(fields.values()):
                break
    if not all(fields.values()):
        raise ValueError("Missing bundle header field in Blueprint")
    return fields

def render_template(template_path: Path, context: dict) -> str:
    text = template_path.read_text(encoding="utf-8")
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

def main() -> int:
    bundle = parse_bundle_header(BLUEPRINT_PATH)
    generated_at = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    context = {**bundle, "GENERATED_AT": generated_at}

    cag_body = render_template(TEMPLATE_DIR / "CAG_instructions.human.md.tpl", context)
    agents_body = render_template(TEMPLATE_DIR / "AGENTS.human.md.tpl", context)

    header = build_header(bundle, generated_at)

    OUTPUT_CAG.write_text(header + cag_body, encoding="utf-8")
    OUTPUT_AGENTS.write_text(header + agents_body, encoding="utf-8")
    print("Generated CAG and AGENTS instruction drafts.")
    return 0

if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
