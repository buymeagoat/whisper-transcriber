import io
from pathlib import Path

import pytest

from api.orm_bootstrap import SessionLocal
from api.models import Job, JobStatusEnum
from tests.conftest import TRANSCRIPTS_DIR


@pytest.mark.asyncio
async def test_create_job_requires_user_header(async_client, stub_job_queue):
    response = await async_client.post(
        "/jobs/",
        files={"file": ("sample.wav", io.BytesIO(b"data"), "audio/wav")},
        data={"model": "small"},
    )

    assert response.status_code == 401
    payload = response.json()
    assert payload["detail"] == "Missing X-User-ID header"


@pytest.mark.asyncio
async def test_job_lifecycle_scoped_to_user(async_client, stub_job_queue, security_headers):
    user_headers = {"X-User-ID": "user-123"}
    user_headers.update(security_headers())

    response = await async_client.post(
        "/jobs/",
        files={"file": ("sample.wav", io.BytesIO(b"data"), "audio/wav")},
        data={"model": "small"},
        headers=user_headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    job_id = body["job_id"]

    with SessionLocal() as session:
        job = session.get(Job, job_id)
        assert job is not None
        assert job.user_id == "user-123"
        assert Path(job.saved_filename).exists()

    list_response = await async_client.get("/jobs/", headers=user_headers)
    assert list_response.status_code == 200
    jobs_payload = list_response.json()
    assert jobs_payload["total"] == 1
    assert jobs_payload["jobs"][0]["job_id"] == job_id

    other_headers = {"X-User-ID": "user-999"}
    other_headers.update(security_headers())

    forbidden_list = await async_client.get("/jobs/", headers=other_headers)
    assert forbidden_list.status_code == 200
    assert forbidden_list.json()["total"] == 0

    forbidden_get = await async_client.get(f"/jobs/{job_id}", headers=other_headers)
    assert forbidden_get.status_code == 404


@pytest.mark.asyncio
async def test_transcript_routes_enforce_ownership(async_client, security_headers):
    owner_headers = security_headers()
    owner_headers["X-User-ID"] = "owner-1"

    job_id = "job-transcript-1"
    transcript_file = TRANSCRIPTS_DIR / f"{job_id}.txt"
    transcript_file.write_text("hello world", encoding="utf-8")

    with SessionLocal() as session:
        job = Job(
            id=job_id,
            original_filename="sample.wav",
            saved_filename="/tmp/sample.wav",
            model="small",
            status=JobStatusEnum.COMPLETED,
            user_id="owner-1",
            transcript_path=str(transcript_file),
        )
        session.add(job)
        session.commit()

    response = await async_client.get(f"/transcripts/{job_id}", headers=owner_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == job_id
    assert payload["transcript"] == "hello world"

    download = await async_client.get(f"/transcripts/{job_id}/download", headers=owner_headers)
    assert download.status_code == 200
    assert download.text == "hello world"

    intruder_headers = security_headers()
    intruder_headers["X-User-ID"] = "intruder"

    denied = await async_client.get(f"/transcripts/{job_id}", headers=intruder_headers)
    assert denied.status_code == 403

    denied_download = await async_client.get(f"/transcripts/{job_id}/download", headers=intruder_headers)
    assert denied_download.status_code == 403
