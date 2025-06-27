import pickle
from unittest.mock import patch

from api.services.job_queue import (
    ThreadJobQueue,
    BrokerJobQueue,
    jobs_queued_total,
    jobs_in_progress,
    job_duration_seconds,
)


def test_thread_job_queue_executes_job():
    calls = []

    start_queued = jobs_queued_total._value.get()
    start_duration = job_duration_seconds._count.get()

    def task():
        calls.append(1)

    q = ThreadJobQueue(1)
    q.enqueue(task)
    q.join()

    assert calls == [1]
    assert jobs_queued_total._value.get() == start_queued + 1
    assert jobs_in_progress._value.get() == 0
    assert job_duration_seconds._count.get() == start_duration + 1


def sample_task():
    return 42


def test_broker_job_queue_sends_task():
    with patch("api.services.celery_app.celery_app.send_task") as send_task:
        q = BrokerJobQueue()
        q.enqueue(sample_task)
        send_task.assert_called_once()
        name = send_task.call_args.args[0]
        payload = send_task.call_args.kwargs["args"][0]
        func = pickle.loads(payload)
        assert name == "run_callable"
        assert func is sample_task


def test_broker_backend_dispatch(monkeypatch):
    monkeypatch.setenv("JOB_QUEUE_BACKEND", "broker")
    import importlib

    with patch("api.services.celery_app.celery_app.send_task") as send_task:
        import api.app_state as app_state

        importlib.reload(app_state)
        app_state.job_queue.enqueue(sample_task)
        send_task.assert_called_once()
