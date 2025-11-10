"""End-to-end API tests exercising authentication, uploads, and job lifecycle."""

from __future__ import annotations

import contextlib
import io
import uuid
from datetime import datetime
from typing import Dict

import pytest

from api.models import Job, JobStatusEnum, User
from api.orm_bootstrap import SessionLocal
from api.paths import storage


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
    assert int(payload["expires_in"]) > 0
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
async def test_legacy_upload_aliases_forward_to_jobs(async_client, admin_token, security_headers, stub_job_queue):
    """Legacy /upload and /api/upload endpoints should behave like /jobs/."""

    headers = security_headers(token=admin_token)

    for path in ("/upload", "/api/upload"):
        response = await async_client.post(
            path,
            data={"model": "small"},
            files={"file": ("alias.wav", io.BytesIO(b"alias audio"), "audio/wav")},
            headers=headers,
        )

        assert response.status_code == 200, f"{path} failed: {response.text}"
        payload = response.json()
        assert "job_id" in payload

    # Ensure the job queue saw submissions from the alias uploads
    assert stub_job_queue.submitted, "Job queue was not invoked through legacy aliases"


@pytest.mark.asyncio
async def test_chunk_initialize_legacy_alias(async_client, admin_token, security_headers):
    """Legacy /uploads/init should map to the canonical initializer."""

    headers = security_headers(token=admin_token)
    payload = {
        "filename": "chunk-legacy.wav",
        "file_size": 1024,
        "model_name": "small",
    }

    response = await async_client.post("/uploads/init", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert "session_id" in body

    # Clean up the in-memory session to avoid test interference
    from api.services.chunked_upload_service import chunked_upload_service

    session_id = body["session_id"]
    await chunked_upload_service.cancel_upload(session_id=session_id, user_id="1")


@pytest.mark.asyncio
async def test_transcript_routes_enforce_ownership(async_client, admin_token, security_headers):
    """Transcript endpoints should return content for owners and reject others."""

    headers = security_headers(token=admin_token)

    transcript_text = "hello transcript"
    job_id = str(uuid.uuid4())
    transcript_path = storage.transcripts_dir / f"{job_id}.txt"
    upload_path = storage.upload_dir / f"{job_id}.wav"
    transcript_path.write_text(transcript_text, encoding="utf-8")
    upload_path.write_bytes(b"audio")

    with SessionLocal() as db:
        admin_user = db.query(User).filter(User.username == "admin").one()
        job = Job(
            id=job_id,
            original_filename="example.wav",
            saved_filename=str(upload_path),
            model="small",
            status=JobStatusEnum.COMPLETED,
            user_id=str(admin_user.id),
            transcript_path=str(transcript_path),
            finished_at=datetime.utcnow(),
        )
        db.add(job)
        db.commit()

    try:
        response = await async_client.get(f"/transcripts/{job_id}", headers=headers)
        assert response.status_code == 200
        payload = response.json()
        assert payload["transcript"] == transcript_text

        download = await async_client.get(f"/transcripts/{job_id}/download", headers=headers)
        assert download.status_code == 200
        assert download.text == transcript_text

        other_username = f"viewer_{uuid.uuid4().hex[:6]}"
        other_password = "ViewerPass123!"
        register = await async_client.post(
            "/register",
            json={"username": other_username, "password": other_password},
            headers=security_headers(include_placeholder_auth=True),
        )
        assert register.status_code == 200

        other_login = await async_client.post(
            "/auth/login",
            json={"username": other_username, "password": other_password},
            headers=security_headers(include_placeholder_auth=True),
        )
        assert other_login.status_code == 200
        other_token = other_login.json()["access_token"]

        forbidden = await async_client.get(
            f"/transcripts/{job_id}",
            headers=security_headers(token=other_token),
        )
        assert forbidden.status_code == 403
    finally:
        with SessionLocal() as db:
            db.query(Job).filter(Job.id == job_id).delete()
            db.commit()
        with contextlib.suppress(FileNotFoundError):
            transcript_path.unlink()
        with contextlib.suppress(FileNotFoundError):
            upload_path.unlink()


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
