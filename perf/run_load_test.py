"""Run the transcription load scenario via k6 and archive the summary."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCENARIO = ROOT / "transcription_scenario.js"
RESULTS_DIR = ROOT / "results"
DEFAULT_OUTPUT = RESULTS_DIR / "latest.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the transcription load test via k6")
    parser.add_argument("--base-url", default=os.environ.get("BASE_URL", "http://localhost:8001"))
    parser.add_argument("--duration", default=os.environ.get("DURATION", "2m"))
    parser.add_argument(
        "--arrival-rate",
        type=float,
        default=float(os.environ.get("ARRIVAL_RATE", 3)),
        help="Target constant-arrival-rate jobs per second",
    )
    parser.add_argument(
        "--pre-allocated-vus",
        type=int,
        default=int(os.environ.get("PRE_ALLOCATED_VUS", 4)),
    )
    parser.add_argument(
        "--max-vus",
        type=int,
        default=int(os.environ.get("MAX_VUS", 12)),
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("WHISPER_MODEL", "tiny"),
        help="Model name to request per job",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=float(os.environ.get("POLL_INTERVAL", 1)),
    )
    parser.add_argument(
        "--max-polls",
        type=int,
        default=int(os.environ.get("MAX_POLLS", 40)),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Path to write the k6 JSON summary",
    )
    parser.add_argument(
        "--scenario",
        default=str(SCENARIO),
        help="Path to the k6 scenario file",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Skip copying the summary to a timestamped archive",
    )
    return parser.parse_args(argv)


def ensure_paths(output_path: Path) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)


def run_k6(args: argparse.Namespace, output_path: Path) -> None:
    env = os.environ.copy()
    env.update(
        {
            "BASE_URL": args.base_url,
            "ARRIVAL_RATE": str(args.arrival_rate),
            "DURATION": args.duration,
            "PRE_ALLOCATED_VUS": str(args.pre_allocated_vus),
            "MAX_VUS": str(args.max_vus),
            "WHISPER_MODEL": args.model,
            "POLL_INTERVAL": str(args.poll_interval),
            "MAX_POLLS": str(args.max_polls),
        }
    )

    cmd = [
        "k6",
        "run",
        "--summary-export",
        str(output_path),
        str(Path(args.scenario).resolve()),
    ]

    print("Running:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True, env=env)
    except FileNotFoundError as exc:
        raise SystemExit(
            "k6 executable not found. Install k6 or make sure it is on PATH before running this script."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc


def archive_results(output_path: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_path = RESULTS_DIR / f"summary_{timestamp}.json"
    shutil.copy2(output_path, archive_path)
    return archive_path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_path = Path(args.output)
    ensure_paths(output_path)

    run_k6(args, output_path)

    if not args.no_archive:
        archived = archive_results(output_path)
        print(f"Archived summary -> {archived}")

    print(f"Summary written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
