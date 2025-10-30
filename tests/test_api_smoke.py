"""FastAPI smoke tests covering authentication, uploads, health, and worker flow."""

from __future__ import annotations

import io
from typing import Dict


def _submit_job(client, admin_token, security_headers) -> str:
    response = client.post(
        "/jobs/",
        data={"model": "small"},
        files={"file": ("sample.wav", io.BytesIO(b"test audio"), "audio/wav")},
        headers=security_headers(token=admin_token),
    )
    assert response.status_code == 200, response.text
    return response.json()["job_id"]

from api.models import Job
from api.orm_bootstrap import SessionLocal


def test_health_endpoint_reports_ok(client) -> None:
    """Health check should confirm the API and database are reachable."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_admin_login_returns_token_and_cookie(client, security_headers) -> None:
    """Login should return a bearer token and set the secure auth cookie."""
    response = client.post(
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


def test_job_upload_and_worker_status_flow(client, admin_token, security_headers, stub_job_queue) -> None:
    """Uploading a file should create a job record and enqueue work."""
    job_id = _submit_job(client, admin_token, security_headers)

    assert stub_job_queue.submitted, "Job queue was not invoked"

    with SessionLocal() as db:
        job = db.query(Job).filter(Job.id == job_id).one()
        assert job.original_filename == "sample.wav"

    detail_response = client.get(f"/jobs/{job_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["job_id"] == job_id
    assert detail["queue_status"] == "pending"


def test_job_listing_includes_recent_submission(
    client, admin_token, security_headers, stub_job_queue
) -> None:
    """Job listings should return newly created jobs."""

    job_id = _submit_job(client, admin_token, security_headers)

    response = client.get("/jobs/")
    assert response.status_code == 200

    payload = response.json()
    jobs = payload.get("jobs", [])
    assert any(job["job_id"] == job_id for job in jobs)


def test_prometheus_metrics_endpoint(client) -> None:
    """The Prometheus metrics endpoint must be readable without auth."""

    client.get("/health")

    response = client.get("/metrics/")
    assert response.status_code == 200
    body = response.text

    assert "whisper_http_requests_total" in body
    assert "whisper_metrics_last_scrape_timestamp" in body
