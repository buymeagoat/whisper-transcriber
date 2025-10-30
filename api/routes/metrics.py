"""Metrics routes for the Whisper Transcriber API."""

from __future__ import annotations

import asyncio
import os
import time
from collections import deque
from typing import Any, Deque, Dict, List, Tuple

import psutil
from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import (  # type: ignore
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

from api.services.redis_cache import get_cache_service
from api.orm_bootstrap import SessionLocal
from api.models import Job, JobStatusEnum
from sqlalchemy import func

router = APIRouter(prefix="/metrics", tags=["metrics"])

# ─── RED Metrics: Rate, Errors, Duration ──────────────────────────────────────
REQUEST_COUNT = Counter(
    "whisper_http_requests_total",
    "Total number of HTTP requests processed",
    ["method", "endpoint", "status_code"],
)
REQUEST_ERRORS = Counter(
    "whisper_http_request_errors_total",
    "Number of HTTP requests that resulted in error responses",
    ["method", "endpoint", "status_code"],
)
REQUEST_DURATION = Histogram(
    "whisper_http_request_duration_seconds",
    "Distribution of HTTP request latencies",
    ["method", "endpoint"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30),
)
REQUESTS_IN_PROGRESS = Gauge(
    "whisper_http_requests_in_progress",
    "Number of HTTP requests currently in progress",
    ["endpoint"],
)

# ─── USE Metrics: Utilization, Saturation, Errors ─────────────────────────────
RESOURCE_UTILIZATION = Gauge(
    "whisper_resource_utilization_ratio",
    "Utilization ratio for critical resources (0-1)",
    ["resource"],
)
RESOURCE_SATURATION = Gauge(
    "whisper_resource_saturation_ratio",
    "Saturation ratio for critical resources (0-1)",
    ["resource"],
)
RESOURCE_ERRORS = Counter(
    "whisper_resource_errors_total",
    "Number of resource level errors encountered",
    ["resource", "kind"],
)
LAST_SCRAPE_TIME = Gauge(
    "whisper_metrics_last_scrape_timestamp",
    "Unix timestamp when metrics were last collected",
)

# ─── Job Queue Metrics ───────────────────────────────────────────────────────
JOB_STATUS_COUNT = Gauge(
    "whisper_jobs_total",
    "Number of transcription jobs by status",
    ["status"],
)

JOB_QUEUE_DEPTH = Gauge(
    "whisper_job_queue_depth",
    "Number of transcription jobs waiting to be processed",
)

JOB_DURATION_SECONDS = Histogram(
    "whisper_job_duration_seconds",
    "Distribution of Whisper job processing durations",
    buckets=(30, 60, 120, 300, 600, 900, 1800, 3600),
)

WORKER_FAILURE_COUNT = Gauge(
    "whisper_worker_failures",
    "Number of jobs currently flagged as worker failures by failure status",
    ["status"],
)

_OBSERVED_JOBS: Deque[str] = deque(maxlen=2048)
_OBSERVED_JOB_SET: set[str] = set()


def record_http_request(method: str, endpoint: str, status_code: int, duration_seconds: float) -> None:
    """Record a completed HTTP request for RED metrics."""

    method = method.upper()
    endpoint = endpoint or "unknown"
    status = str(status_code)

    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(max(duration_seconds, 0.0))

    if status_code >= 400:
        REQUEST_ERRORS.labels(method=method, endpoint=endpoint, status_code=status).inc()


async def _update_system_metrics() -> None:
    """Refresh USE metrics for system resources."""

    try:
        cpu_ratio = psutil.cpu_percent(interval=None) / 100.0
        RESOURCE_UTILIZATION.labels(resource="cpu").set(cpu_ratio)
        RESOURCE_SATURATION.labels(resource="cpu").set(cpu_ratio)
    except Exception:  # pragma: no cover - psutil edge case
        RESOURCE_ERRORS.labels(resource="cpu", kind="collection").inc()

    try:
        virtual_memory = psutil.virtual_memory()
        memory_ratio = virtual_memory.percent / 100.0
        RESOURCE_UTILIZATION.labels(resource="memory").set(memory_ratio)
        RESOURCE_SATURATION.labels(resource="memory").set(memory_ratio)
    except Exception:  # pragma: no cover - psutil edge case
        RESOURCE_ERRORS.labels(resource="memory", kind="collection").inc()

    try:
        disk = psutil.disk_usage(os.getcwd())
        disk_ratio = disk.percent / 100.0
        RESOURCE_UTILIZATION.labels(resource="disk").set(disk_ratio)
        RESOURCE_SATURATION.labels(resource="disk").set(disk_ratio)
    except Exception:  # pragma: no cover - psutil edge case
        RESOURCE_ERRORS.labels(resource="disk", kind="collection").inc()

    await _update_redis_metrics()
    await _update_job_metrics()
    LAST_SCRAPE_TIME.set(time.time())


async def _update_redis_metrics() -> None:
    """Capture Redis utilisation and saturation."""

    try:
        cache_service = await get_cache_service()
        redis_pool = getattr(cache_service, "redis_pool", None)
        if not redis_pool:
            RESOURCE_SATURATION.labels(resource="redis_connections").set(0.0)
            RESOURCE_UTILIZATION.labels(resource="redis_memory").set(0.0)
            return

        info: Dict[str, Any] = await redis_pool.info(section="memory")
        clients = await redis_pool.info(section="clients")

        used_memory = float(info.get("used_memory", 0.0))
        maxmemory = float(info.get("maxmemory", 0.0))
        if maxmemory > 0:
            RESOURCE_UTILIZATION.labels(resource="redis_memory").set(min(used_memory / maxmemory, 1.0))
        else:
            RESOURCE_UTILIZATION.labels(resource="redis_memory").set(0.0)

        connected_clients = float(clients.get("connected_clients", 0.0))
        max_clients = float(clients.get("maxclients", 0.0))
        if max_clients:
            RESOURCE_SATURATION.labels(resource="redis_connections").set(min(connected_clients / max_clients, 1.0))
        else:
            RESOURCE_SATURATION.labels(resource="redis_connections").set(0.0)
    except Exception:  # pragma: no cover - defensive guard
        RESOURCE_ERRORS.labels(resource="redis", kind="collection").inc()


def _remember_job(job_id: str) -> bool:
    """Return True if job_id has not yet been observed for duration metrics."""

    if job_id in _OBSERVED_JOB_SET:
        return False

    if len(_OBSERVED_JOBS) == _OBSERVED_JOBS.maxlen:
        oldest = _OBSERVED_JOBS.popleft()
        _OBSERVED_JOB_SET.discard(oldest)

    _OBSERVED_JOBS.append(job_id)
    _OBSERVED_JOB_SET.add(job_id)
    return True


async def _update_job_metrics() -> None:
    """Collect job queue metrics from the database."""

    def _collect() -> Tuple[Dict[str, int], List[Tuple[str, float]]]:
        with SessionLocal() as session:
            status_rows = (
                session.query(Job.status, func.count(Job.id))
                .group_by(Job.status)
                .all()
            )
            status_counts = {
                (status.value if isinstance(status, JobStatusEnum) else str(status)): int(count)
                for status, count in status_rows
            }

            duration_rows = (
                session.query(Job.id, Job.started_at, Job.finished_at)
                .filter(Job.started_at.isnot(None), Job.finished_at.isnot(None))
                .order_by(Job.finished_at.desc())
                .limit(512)
            )

            durations: List[Tuple[str, float]] = []
            for job_id, started_at, finished_at in duration_rows:
                assert started_at is not None and finished_at is not None
                duration = max((finished_at - started_at).total_seconds(), 0.0)
                durations.append((job_id, duration))

            return status_counts, durations

    try:
        status_counts, durations = await asyncio.to_thread(_collect)
    except Exception:  # pragma: no cover - defensive guard
        return

    for status in JobStatusEnum:
        count = status_counts.get(status.value, 0)
        JOB_STATUS_COUNT.labels(status=status.value).set(count)

    queued = status_counts.get(JobStatusEnum.QUEUED.value, 0)
    JOB_QUEUE_DEPTH.set(queued)

    failure_statuses = [s for s in JobStatusEnum if s.value.startswith("failed")]
    for status in failure_statuses:
        count = status_counts.get(status.value, 0)
        WORKER_FAILURE_COUNT.labels(status=status.value).set(count)

    for job_id, duration in durations:
        if _remember_job(job_id):
            JOB_DURATION_SECONDS.observe(duration)


@router.get("/")
async def get_metrics() -> Response:
    """Expose Prometheus metrics for scraping."""

    await _update_system_metrics()
    metrics_payload = await asyncio.to_thread(generate_latest)
    return Response(content=metrics_payload, media_type=CONTENT_TYPE_LATEST)


__all__ = [
    "router",
    "record_http_request",
    "REQUESTS_IN_PROGRESS",
]
