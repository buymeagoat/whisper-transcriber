import pickle
from unittest.mock import patch

from api.services.job_queue import ThreadJobQueue, BrokerJobQueue


def test_thread_job_queue_executes_job():
    calls = []

    def task():
        calls.append(1)

    q = ThreadJobQueue(1)
    q.enqueue(task)
    q.join()
    assert calls == [1]


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
