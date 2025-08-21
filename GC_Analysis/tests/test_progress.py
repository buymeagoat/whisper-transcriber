import threading
import importlib

from api.routes import progress


class DummyWebSocket:
    def __init__(self):
        self.messages = []

    async def send_json(self, data):
        self.messages.append(data)


def test_concurrent_progress_updates():
    importlib.reload(progress)
    job_id = "job1"
    ws = DummyWebSocket()
    with progress.progress_lock:
        progress.progress_connections[job_id] = {ws}

    errors = []

    def worker():
        try:
            progress.send_progress_update(job_id, "processing")
        except Exception as exc:  # pragma: no cover - ensure no exceptions
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert len(ws.messages) == 5
