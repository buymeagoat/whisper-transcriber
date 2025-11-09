"""Smoke tests for the Prometheus metrics endpoint."""

from __future__ import annotations

from typing import Set

import pytest
from prometheus_client.parser import text_string_to_metric_families

EXPECTED_METRICS: Set[str] = {
    "whisper_http_requests",
    "whisper_http_request_duration_seconds",
    "whisper_http_requests_in_progress",
    "whisper_http_request_errors",
    "whisper_jobs_total",
    "whisper_job_queue_depth",
    "whisper_job_duration_seconds",
    "whisper_worker_failures",
    "whisper_resource_utilization_ratio",
    "whisper_resource_saturation_ratio",
    "whisper_resource_errors",
    "whisper_metrics_last_scrape_timestamp",
}


@pytest.mark.asyncio()
async def test_metrics_endpoint_returns_expected_series(async_client):
    """The /metrics endpoint should respond and expose the documented series."""

    # Issue a basic request so RED metrics counters are initialised.
    health_response = await async_client.get("/health/livez")
    assert health_response.status_code == 200

    response = await async_client.get("/metrics/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")

    observed_names = {
        family.name for family in text_string_to_metric_families(response.text)
    }

    missing = sorted(EXPECTED_METRICS.difference(observed_names))
    assert not missing, f"Missing expected metrics: {missing}"


@pytest.mark.asyncio()
async def test_metrics_endpoint_includes_histogram_buckets(async_client):
    """Histograms should expose bucket samples so latency quantiles can be computed."""

    warmup_response = await async_client.get("/health/livez")
    assert warmup_response.status_code == 200

    response = await async_client.get("/metrics/")
    assert response.status_code == 200

    families = list(text_string_to_metric_families(response.text))
    histogram = next(
        (family for family in families if family.name == "whisper_http_request_duration_seconds"),
        None,
    )
    assert histogram is not None, "Latency histogram was not exported"

    bucket_samples = [sample for sample in histogram.samples if sample.name.endswith("_bucket")]
    assert bucket_samples, "Expected histogram buckets to be present in the metrics payload"
