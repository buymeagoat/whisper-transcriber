import pytest
from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException

from api.models import Job, JobStatusEnum
from api.orm_bootstrap import SessionLocal
from api.paths import storage
from api.services.consolidated_transcript_service import ConsolidatedTranscriptService


@pytest.mark.asyncio
async def test_transcript_service_enforces_ownership(tmp_path):
    service = ConsolidatedTranscriptService()
    job_id = str(uuid4())
    transcript_path = storage.transcripts_dir / f"{job_id}.txt"
    transcript_path.write_text("owned transcript", encoding="utf-8")

    with SessionLocal() as db:
        job = Job(
            id=job_id,
            user_id="owner-1",
            original_filename="audio.wav",
            saved_filename=str(tmp_path / "audio.wav"),
            model="small",
            status=JobStatusEnum.COMPLETED,
            transcript_path=str(transcript_path),
            created_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        with pytest.raises(HTTPException) as exc:
            await service.get_transcript(job_id, "intruder", db)
        assert exc.value.status_code == 403

        result = await service.get_transcript(job_id, "owner-1", db)
        assert result["job_id"] == job_id
        assert result["transcript"] == "owned transcript"
        assert result["status"] == JobStatusEnum.COMPLETED.value

        listing = await service.get_user_transcripts("owner-1", db)
        assert listing["total"] >= 1
        assert any(item["job_id"] == job_id for item in listing["results"])

        db.delete(job)
        db.commit()

    transcript_path.unlink(missing_ok=True)
