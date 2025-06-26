from pathlib import Path

from api.orm_bootstrap import SessionLocal
from api.models import Job, JobStatusEnum
from api.paths import TRANSCRIPTS_DIR


def test_job_lifecycle(client, sample_wav):
    with sample_wav.open("rb") as f:
        resp = client.post(
            "/jobs",
            data={"model": "base"},
            files={"file": ("test.wav", f, "audio/wav")},
        )
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    resp = client.get("/jobs")
    assert any(j["id"] == job_id for j in resp.json())

    resp = client.get(f"/jobs/{job_id}")
    assert resp.status_code == 200

    resp = client.post(f"/jobs/{job_id}/restart")
    assert resp.json()["status"] == "restarted"

    transcript = TRANSCRIPTS_DIR / job_id / "out.srt"
    transcript.parent.mkdir(parents=True, exist_ok=True)
    transcript.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n")
    with SessionLocal() as db:
        job = db.query(Job).get(job_id)
        job.status = JobStatusEnum.COMPLETED
        job.transcript_path = str(transcript)
        db.commit()

    resp = client.get(f"/jobs/{job_id}/download")
    assert resp.status_code == 200
    assert "attachment" in resp.headers.get("content-disposition", "")

    resp = client.delete(f"/jobs/{job_id}")
    assert resp.json()["status"] == "deleted"
    with SessionLocal() as db:
        assert db.query(Job).get(job_id) is None
