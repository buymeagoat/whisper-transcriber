import io
import os

import pytest
from fastapi import UploadFile

from api.models import Job
from api.orm_bootstrap import SessionLocal
from api.services.chunked_upload_service import ChunkedUploadService
from api.services.consolidated_upload_service import ConsolidatedUploadService


@pytest.mark.asyncio
async def test_direct_upload_enqueues_celery_task(stub_job_queue):
    service = ConsolidatedUploadService()
    file_bytes = b"dummy audio data"
    upload = UploadFile(
        filename="direct.wav",
        file=io.BytesIO(file_bytes),
        headers={"content-type": "audio/wav"},
    )

    try:
        with SessionLocal() as db:
            result = await service.handle_direct_upload(
                upload,
                user_id="user-123",
                db=db,
                model_name="small",
                language="en",
            )

        assert stub_job_queue.submitted, "Job queue should receive a submission"
        submission = stub_job_queue.submitted[-1]
        assert submission["task_name"] == "transcribe_audio"
        assert submission["kwargs"]["job_id"] == result["job_id"]
        saved_path = submission["kwargs"]["file_path"]
        assert saved_path.endswith(".wav")
        assert os.path.exists(saved_path)

        with SessionLocal() as verify_db:
            job = verify_db.get(Job, result["job_id"])
            assert job is not None
            assert job.user_id == "user-123"
    finally:
        await upload.close()
        with SessionLocal() as cleanup_db:
            job = cleanup_db.get(Job, result["job_id"])
            if job:
                cleanup_db.delete(job)
                cleanup_db.commit()

        if "saved_path" in locals() and os.path.exists(saved_path):
            os.remove(saved_path)


@pytest.mark.asyncio
async def test_chunked_upload_enqueues_celery_task(stub_job_queue):
    service = ChunkedUploadService()
    file_bytes = b"chunked audio payload"
    file_size = len(file_bytes)

    init = await service.initialize_upload(
        user_id="user-456",
        filename="chunked.wav",
        file_size=file_size,
        model_name="base",
        language="en",
    )

    session_id = init["session_id"]

    upload_result = await service.upload_chunk(
        session_id=session_id,
        chunk_number=0,
        chunk_data=file_bytes,
        user_id="user-456",
    )

    assert upload_result["status"] == "uploaded"

    finalize = await service.finalize_upload(session_id=session_id, user_id="user-456")

    assert finalize["status"] == "completed"
    assert "job_id" in finalize

    assert stub_job_queue.submitted, "Job queue should receive a submission"
    submission = stub_job_queue.submitted[-1]
    assert submission["task_name"] == "transcribe_audio"
    assert submission["kwargs"]["job_id"] == finalize["job_id"]
    saved_path = submission["kwargs"]["file_path"]
    assert saved_path.endswith("chunked.wav")
    assert os.path.exists(saved_path)

    with SessionLocal() as verify_db:
        job = verify_db.get(Job, finalize["job_id"])
        assert job is not None
        assert job.user_id == "user-456"

    with SessionLocal() as cleanup_db:
        job = cleanup_db.get(Job, finalize["job_id"])
        if job:
            cleanup_db.delete(job)
            cleanup_db.commit()

    if os.path.exists(saved_path):
        os.remove(saved_path)
