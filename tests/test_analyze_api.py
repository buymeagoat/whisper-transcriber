from datetime import datetime

from api.orm_bootstrap import SessionLocal
from api.models import Job, JobStatusEnum, TranscriptMetadata
from api.paths import TRANSCRIPTS_DIR


def test_analyze_endpoint(client, sample_wav):
    with sample_wav.open("rb") as f:
        resp = client.post(
            "/jobs",
            data={"model": "base"},
            files={"file": ("file.wav", f, "audio/wav")},
        )
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    transcript = TRANSCRIPTS_DIR / job_id / "out.srt"
    transcript.parent.mkdir(parents=True, exist_ok=True)
    transcript.write_text("Hello world. This is a test transcript. Hello again.")
    with SessionLocal() as db:
        job = db.query(Job).get(job_id)
        job.status = JobStatusEnum.COMPLETED
        job.transcript_path = str(transcript)
        db.add(
            TranscriptMetadata(
                job_id=job_id,
                tokens=0,
                duration=0,
                abstract="",
                generated_at=datetime.utcnow(),
            )
        )
        db.commit()

    resp = client.post(f"/jobs/{job_id}/analyze")
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data and "keywords" in data
    with SessionLocal() as db:
        meta = db.query(TranscriptMetadata).filter_by(job_id=job_id).first()
        assert meta.summary == data["summary"]
