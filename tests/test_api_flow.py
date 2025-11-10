"""End-to-end API tests exercising authentication, uploads, and job lifecycle."""

from __future__ import annotations

import io
from typing import Dict

import pytest

from api.models import Job
from api.orm_bootstrap import SessionLocal


@pytest.mark.asyncio
async def test_admin_login_returns_token_and_cookie(async_client, security_headers):
    """Login should return a bearer token and set the secure auth cookie."""

    response = await async_client.post(
        "/auth/login",
        json={"username": "admin", "password": "super-secure-test-password-!123"},
        headers=security_headers(include_placeholder_auth=True),
    )
    assert response.status_code == 200

    payload: Dict[str, str] = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["expires_in"] > 0
    assert "auth_token" in response.cookies


async def _submit_job(async_client, admin_token, security_headers, stub_job_queue) -> str:
    response = await async_client.post(
        "/jobs/",
        data={"model": "small"},
        files={"file": ("sample.wav", io.BytesIO(b"test audio"), "audio/wav")},
        headers=security_headers(token=admin_token),
    )
    assert response.status_code == 200, response.text
    assert stub_job_queue.submitted, "Job queue was not invoked"
    return response.json()["job_id"]


@pytest.mark.asyncio
async def test_job_upload_and_worker_status_flow(async_client, admin_token, security_headers, stub_job_queue):
    """Uploading a file should create a job record and enqueue work."""

    job_id = await _submit_job(async_client, admin_token, security_headers, stub_job_queue)

    with SessionLocal() as db:
        job = db.query(Job).filter(Job.id == job_id).one()
        assert job.original_filename == "sample.wav"

    detail_response = await async_client.get(f"/jobs/{job_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["job_id"] == job_id
    assert detail["queue_status"] == "pending"


@pytest.mark.asyncio
async def test_job_listing_includes_recent_submission(async_client, admin_token, security_headers, stub_job_queue):
    """Job listings should return newly created jobs."""

    job_id = await _submit_job(async_client, admin_token, security_headers, stub_job_queue)

    response = await async_client.get("/jobs/")
    assert response.status_code == 200

    payload = response.json()
    jobs = payload.get("jobs", [])
    assert any(job["job_id"] == job_id for job in jobs)


@pytest.mark.asyncio
async def test_job_upload_accepts_legacy_header(async_client, security_headers, stub_job_queue):
    """Legacy X-User-ID header should continue to authenticate uploads."""

    headers = security_headers()
    headers["X-User-ID"] = "legacy-user"

    response = await async_client.post(
        "/jobs/",
        data={"model": "small"},
        files={"file": ("legacy.wav", io.BytesIO(b"legacy audio"), "audio/wav")},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["user_id"] == "legacy-user"
    assert stub_job_queue.submitted, "Job queue did not receive the legacy upload"


@pytest.mark.asyncio
async def test_health_endpoints_report_ready(async_client):
    """Liveness and readiness probes should respond with healthy payloads."""

    livez = await async_client.get("/health/livez")
    assert livez.status_code == 200
    assert livez.json()["status"] == "ok"

    readyz = await async_client.get("/health/readyz")
    assert readyz.status_code == 200
    payload = readyz.json()
    assert payload["status"] in {"ready", "degraded"}
    assert "database" in payload["checks"]
    assert "redis" in payload["checks"]
    assert "models" in payload["checks"]


@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint(async_client):
    """The Prometheus metrics endpoint must be readable without auth."""

    await async_client.get("/health/livez")

    response = await async_client.get("/metrics/")
    assert response.status_code == 200
    body = response.text

    assert "whisper_http_requests_total" in body
    assert "whisper_metrics_last_scrape_timestamp" in body
