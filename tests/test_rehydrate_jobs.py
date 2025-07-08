import importlib

from api.orm_bootstrap import SessionLocal
from api.models import Job, JobStatusEnum
import api.main as main


def test_rehydrated_jobs_are_enqueued(temp_db, temp_dirs, monkeypatch):
    importlib.reload(main)

    job_id = "job1"
    with SessionLocal() as db:
        db.add(
            Job(
                id=job_id,
                original_filename="a.wav",
                saved_filename="a.wav",
                model="base",
                status=JobStatusEnum.QUEUED,
            )
        )
        db.commit()

    enqueued = []
    monkeypatch.setattr(
        main.app_state.job_queue, "enqueue", lambda f: enqueued.append(f)
    )

    calls = []

    def fake_handle(*args, **kwargs):
        calls.append(kwargs.get("start_thread"))

    monkeypatch.setattr(main, "handle_whisper", fake_handle)

    main.rehydrate_incomplete_jobs()

    assert calls == []
    assert len(enqueued) == 1

    enqueued[0]()
    assert calls == [False]
