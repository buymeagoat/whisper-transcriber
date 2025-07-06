from pathlib import Path

from datetime import datetime

from api.orm_bootstrap import SessionLocal
from api.models import Job, JobStatusEnum, TranscriptMetadata
from api.paths import TRANSCRIPTS_DIR
from api.errors import ErrorCode
import api.routes.jobs as jobs


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


def test_submit_invalid_model_api(client, sample_wav):
    with sample_wav.open("rb") as f:
        resp = client.post(
            "/jobs",
            data={"model": "bogus"},
            files={"file": ("bad.wav", f, "audio/wav")},
        )
    assert resp.status_code == 400


def test_list_jobs_search_filter(client, sample_wav):
    with sample_wav.open("rb") as f:
        resp = client.post(
            "/jobs",
            data={"model": "base"},
            files={"file": ("alpha.wav", f, "audio/wav")},
        )
    job_id_a = resp.json()["job_id"]

    with sample_wav.open("rb") as f:
        resp = client.post(
            "/jobs",
            data={"model": "base"},
            files={"file": ("beta.wav", f, "audio/wav")},
        )
    job_id_b = resp.json()["job_id"]

    with SessionLocal() as db:
        db.add(
            TranscriptMetadata(
                job_id=job_id_a,
                tokens=1,
                duration=1,
                abstract="a",
                keywords="meeting alpha",
                generated_at=datetime.utcnow(),
            )
        )
        db.add(
            TranscriptMetadata(
                job_id=job_id_b,
                tokens=1,
                duration=1,
                abstract="b",
                keywords="beta notes",
                generated_at=datetime.utcnow(),
            )
        )
        db.commit()

    resp = client.get("/jobs?search=alpha")
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == job_id_a

    resp = client.get(f"/jobs?search={job_id_b[:8]}")
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == job_id_b

    resp = client.get("/jobs?search=meeting")
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == job_id_a

    resp = client.get("/jobs?search=notes")
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == job_id_b


def test_list_jobs_status_filter(client, sample_wav):
    with sample_wav.open("rb") as f:
        resp = client.post(
            "/jobs",
            data={"model": "base"},
            files={"file": ("a.wav", f, "audio/wav")},
        )
    job_a = resp.json()["job_id"]

    with sample_wav.open("rb") as f:
        resp = client.post(
            "/jobs",
            data={"model": "base"},
            files={"file": ("b.wav", f, "audio/wav")},
        )
    job_b = resp.json()["job_id"]

    with sample_wav.open("rb") as f:
        resp = client.post(
            "/jobs",
            data={"model": "base"},
            files={"file": ("c.wav", f, "audio/wav")},
        )
    job_c = resp.json()["job_id"]

    with SessionLocal() as db:
        db.query(Job).filter_by(id=job_b).update({"status": JobStatusEnum.COMPLETED})
        db.query(Job).filter_by(id=job_c).update(
            {"status": JobStatusEnum.FAILED_TIMEOUT}
        )
        db.commit()

    resp = client.get("/jobs?status=queued")
    assert [j["id"] for j in resp.json()] == [job_a]

    resp = client.get("/jobs?status=completed")
    assert [j["id"] for j in resp.json()] == [job_b]

    resp = client.get("/jobs?status=failed")
    assert [j["id"] for j in resp.json()] == [job_c]

    resp = client.get("/jobs?status=queued|completed")
    assert {j["id"] for j in resp.json()} == {job_a, job_b}


def test_list_jobs_failed_statuses(client, sample_wav):
    fail_statuses = [
        status for status in JobStatusEnum if status.value.startswith("failed")
    ]

    job_ids = []
    for st in fail_statuses:
        with sample_wav.open("rb") as f:
            resp = client.post(
                "/jobs",
                data={"model": "base"},
                files={"file": (f"{st.value}.wav", f, "audio/wav")},
            )
        job_ids.append(resp.json()["job_id"])

    with SessionLocal() as db:
        for jid, st in zip(job_ids, fail_statuses):
            db.query(Job).filter_by(id=jid).update({"status": st})
        db.commit()

    resp = client.get("/jobs?status=failed")
    assert {j["id"] for j in resp.json()} == set(job_ids)


def test_upload_path_traversal(client, sample_wav):
    with sample_wav.open("rb") as f:
        resp = client.post(
            "/jobs",
            data={"model": "base"},
            files={"file": ("../evil.wav", f, "audio/wav")},
        )

    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    from api.paths import UPLOAD_DIR

    files = list(UPLOAD_DIR.iterdir())
    assert len(files) == 1
    saved = files[0]
    assert saved.is_file()
    assert saved.is_relative_to(UPLOAD_DIR)
    assert saved.name.startswith(f"{job_id}_")
    assert ".." not in saved.name


def test_transcript_view_missing_file(client, sample_wav):
    with sample_wav.open("rb") as f:
        resp = client.post(
            "/jobs",
            data={"model": "base"},
            files={"file": ("file.wav", f, "audio/wav")},
        )
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    transcript_path = TRANSCRIPTS_DIR / job_id / "out.srt"
    transcript_path.parent.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as db:
        job = db.query(Job).get(job_id)
        job.status = JobStatusEnum.COMPLETED
        job.transcript_path = str(transcript_path)
        db.commit()

    resp = client.get(f"/transcript/{job_id}/view")
    assert resp.status_code == 404
    assert "Transcript file not found" in resp.text
    assert str(transcript_path) not in resp.text


def test_job_submit_save_error(client, sample_wav, monkeypatch):
    def fail_save(fileobj, name):
        raise OSError("disk error")

    monkeypatch.setattr(jobs.storage, "save_upload", fail_save)
    with sample_wav.open("rb") as f:
        resp = client.post(
            "/jobs",
            data={"model": "base"},
            files={"file": ("in.wav", f, "audio/wav")},
        )

    assert resp.status_code == 500
    assert resp.json()["code"] == ErrorCode.FILE_SAVE_FAILED
