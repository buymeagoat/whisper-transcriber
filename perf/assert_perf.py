
"""Compare nightly k6 results with stored baseline tolerances."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASELINE_PATH = ROOT / "baseline.json"
DEFAULT_SUMMARY = ROOT / "results" / "latest.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Performance summary missing: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_metric(summary: dict, metric: str, stat: str) -> float:
    metrics = summary.get("metrics", {})
    metric_body = metrics.get(metric)
    if not metric_body:
        raise KeyError(f"Metric '{metric}' missing from summary")
    value = metric_body.get(stat)
    if value is None:
        raise KeyError(f"Statistic '{stat}' missing from metric '{metric}'")
    return float(value)


def compare(latest: dict, baseline: dict) -> list[str]:
    failures: list[str] = []
    tol = baseline.get("tolerances", {})
    base_metrics = baseline.get("metrics", {})

    comparisons = [
        ("http_req_duration", "avg", "http_req_duration_ms_avg", 1000.0),
        ("http_req_duration", "p(95)", "http_req_duration_ms_p95", 1000.0),
        ("transcription_latency_seconds", "avg", "transcription_latency_seconds_avg", 1.0),
        ("transcription_latency_seconds", "p(95)", "transcription_latency_seconds_p95", 1.0),
    ]

    for metric_name, stat, baseline_key, scale in comparisons:
        latest_value = get_metric(latest, metric_name, stat)
        baseline_value = base_metrics.get(baseline_key)
        tolerance = tol.get(baseline_key)
        if baseline_value is None or tolerance is None:
            failures.append(f"Missing baseline entry for {baseline_key}")
            continue
        allowed = baseline_value * tolerance
        if latest_value * scale > allowed:
            failures.append(
                f"{metric_name} {stat} {latest_value * scale:.2f} exceeded allowed {allowed:.2f}"
            )

    success_rate = get_metric(latest, "transcription_success_rate", "rate")
    min_success = tol.get("transcription_success_rate")
    if min_success is not None and success_rate < min_success:
        failures.append(
            f"transcription_success_rate {success_rate:.3f} below minimum {min_success:.3f}"
        )

    return failures


def main(summary_path: str | None = None) -> int:
    summary_file = Path(summary_path) if summary_path else DEFAULT_SUMMARY
    summary = load_json(summary_file)
    baseline = load_json(BASELINE_PATH)
    failures = compare(summary, baseline)

    if failures:
        for failure in failures:
            print(f"::error::{failure}")
        return 1

    print("Performance metrics within baseline tolerances")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
