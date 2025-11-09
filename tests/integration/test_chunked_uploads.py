"""Integration coverage for the chunked upload REST workflow."""

from __future__ import annotations

import os

import pytest


@pytest.mark.asyncio
async def test_finalize_enqueues_transcription_task(async_client, security_headers, stub_job_queue):
    """Uploading a chunk and finalizing should enqueue ``transcribe_audio``."""

    stub_job_queue.submitted.clear()

    headers = security_headers(include_placeholder_auth=True)
    headers["X-User-ID"] = "chunk-user"

    chunk_bytes = b"chunked audio payload"

    init_response = await async_client.post(
        "/uploads/initialize",
        json={
            "filename": "chunked.wav",
            "file_size": len(chunk_bytes),
            "model_name": "small",
            "language": "en",
        },
        headers=headers,
    )
    assert init_response.status_code == 200, init_response.text
    init_payload = init_response.json()
    session_id = init_payload["session_id"]

    upload_response = await async_client.post(
        f"/uploads/{session_id}/chunks/0",
        files={"chunk_data": ("chunk.bin", chunk_bytes, "application/octet-stream")},
        headers=headers,
    )
    assert upload_response.status_code == 200, upload_response.text
    assert upload_response.json()["status"] == "uploaded"

    finalize_response = await async_client.post(
        f"/uploads/{session_id}/finalize",
        headers=headers,
    )
    assert finalize_response.status_code == 200, finalize_response.text
    finalize_payload = finalize_response.json()
    assert finalize_payload["status"] == "completed"

    assert stub_job_queue.submitted, "Expected a Celery task submission"
    submission = stub_job_queue.submitted[-1]
    assert submission["task_name"] == "transcribe_audio"
    assert submission["kwargs"]["job_id"] == finalize_payload["job_id"]

    saved_path = submission["kwargs"]["file_path"]
    assert saved_path.endswith("chunked.wav")
    assert os.path.exists(saved_path)

    if os.path.exists(saved_path):
        os.remove(saved_path)


@pytest.mark.asyncio
async def test_rejects_empty_chunk_without_enqueuing(async_client, security_headers, stub_job_queue):
    """Empty chunk uploads should be rejected and no task should be queued."""

    stub_job_queue.submitted.clear()

    headers = security_headers(include_placeholder_auth=True)
    headers["X-User-ID"] = "chunk-negative"

    init_response = await async_client.post(
        "/uploads/initialize",
        json={
            "filename": "bad.wav",
            "file_size": 1024,
            "model_name": "small",
            "language": "en",
        },
        headers=headers,
    )
    assert init_response.status_code == 200, init_response.text
    session_id = init_response.json()["session_id"]

    bad_chunk_response = await async_client.post(
        f"/uploads/{session_id}/chunks/0",
        files={"chunk_data": ("chunk.bin", b"", "application/octet-stream")},
        headers=headers,
    )
    assert bad_chunk_response.status_code == 400
    assert bad_chunk_response.json()["detail"] == "Empty chunk data"

    finalize_response = await async_client.post(
        f"/uploads/{session_id}/finalize",
        headers=headers,
    )
    assert finalize_response.status_code == 200, finalize_response.text
    finalize_payload = finalize_response.json()
    assert finalize_payload["status"] == "incomplete"
    assert finalize_payload["missing_chunks"] == [0]

    assert not stub_job_queue.submitted
