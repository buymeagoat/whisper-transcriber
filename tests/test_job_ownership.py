import io
from pathlib import Path

import pytest

from api.orm_bootstrap import SessionLocal
from api.models import Job, JobStatusEnum, User
from tests.conftest import TRANSCRIPTS_DIR


@pytest.mark.asyncio
async def test_create_job_requires_authentication(async_client, stub_job_queue):
    response = await async_client.post(
        "/jobs/",
        files={"file": ("sample.wav", io.BytesIO(b"data"), "audio/wav")},
        data={"model": "small"},
    )

    assert response.status_code == 401
    payload = response.json()
    assert payload["detail"] == "Authentication required"


@pytest.mark.asyncio
async def test_job_lifecycle_scoped_to_user(
    async_client,
    admin_token,
    stub_job_queue,
    security_headers,
    standard_user_credentials,
):
    admin_headers = security_headers(token=admin_token)

    response = await async_client.post(
        "/jobs/",
        files={"file": ("sample.wav", io.BytesIO(b"data"), "audio/wav")},
        data={"model": "small"},
        headers=admin_headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    job_id = body["job_id"]

    with SessionLocal() as session:
        job = session.get(Job, job_id)
        assert job is not None
        admin = session.query(User).filter(User.username == "admin").one()
        assert job.user_id == str(admin.id)
        assert Path(job.saved_filename).exists()

    list_response = await async_client.get("/jobs/", headers=admin_headers)
    assert list_response.status_code == 200
    jobs_payload = list_response.json()
    assert jobs_payload["total"] >= 1
    job_ids = {job["job_id"] for job in jobs_payload["jobs"]}
    assert job_id in job_ids

    username, password = standard_user_credentials
    login_response = await async_client.post(
        "/auth/login",
        json={"username": username, "password": password},
        headers=security_headers(include_placeholder_auth=True),
    )
    assert login_response.status_code == 200, login_response.text
    other_token = login_response.json()["access_token"]
    other_headers = security_headers(token=other_token)

    forbidden_list = await async_client.get("/jobs/", headers=other_headers)
    assert forbidden_list.status_code == 200
    assert forbidden_list.json()["total"] == 0

    forbidden_get = await async_client.get(f"/jobs/{job_id}", headers=other_headers)
    assert forbidden_get.status_code == 404


@pytest.mark.asyncio
async def test_transcript_routes_enforce_ownership(
    async_client,
    admin_token,
    security_headers,
    standard_user_credentials,
):
    owner_headers = security_headers(token=admin_token)

    job_id = "job-transcript-1"
    transcript_file = TRANSCRIPTS_DIR / f"{job_id}.txt"
    transcript_file.write_text("hello world", encoding="utf-8")

    with SessionLocal() as session:
        admin = session.query(User).filter(User.username == "admin").one()
        job = Job(
            id=job_id,
            original_filename="sample.wav",
            saved_filename="/tmp/sample.wav",
            model="small",
            status=JobStatusEnum.COMPLETED,
            user_id=str(admin.id),
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

    username, password = standard_user_credentials
    login_response = await async_client.post(
        "/auth/login",
        json={"username": username, "password": password},
        headers=security_headers(include_placeholder_auth=True),
    )
    assert login_response.status_code == 200, login_response.text
    intruder_headers = security_headers(token=login_response.json()["access_token"])

    denied = await async_client.get(f"/transcripts/{job_id}", headers=intruder_headers)
    assert denied.status_code == 403

    denied_download = await async_client.get(f"/transcripts/{job_id}/download", headers=intruder_headers)
    assert denied_download.status_code == 403


@pytest.mark.asyncio
async def test_multi_user_toggle_blocks_non_admin(async_client, security_headers, standard_user_credentials):
    from api.settings import settings as app_settings

    username, password = standard_user_credentials

    login_response = await async_client.post(
        "/auth/login",
        json={"username": username, "password": password},
        headers=security_headers(include_placeholder_auth=True),
    )
    assert login_response.status_code == 200, login_response.text
    user_headers = security_headers(token=login_response.json()["access_token"])

    original_flag = app_settings.multi_user_mode_enabled
    app_settings.multi_user_mode_enabled = False

    try:
        response = await async_client.get("/jobs/", headers=user_headers)
        assert response.status_code == 403
        detail = response.json().get("detail")
        assert detail == "Multi-user mode is disabled"
    finally:
        app_settings.multi_user_mode_enabled = original_flag
