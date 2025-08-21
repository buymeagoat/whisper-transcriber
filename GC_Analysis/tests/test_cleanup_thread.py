import importlib
import time
import threading

import api.app_state as app_state


def test_start_and_stop_cleanup_thread(monkeypatch):
    importlib.reload(app_state)
    calls = []
    monkeypatch.setattr(app_state, "cleanup_once", lambda: calls.append(1))
    app_state.cleanup_stop_event = threading.Event()

    thread = app_state.start_cleanup_thread(interval=0.01)
    time.sleep(0.05)
    assert len(calls) >= 1

    app_state.stop_cleanup_thread()
    thread.join(timeout=0.2)
    call_count = len(calls)
    time.sleep(0.05)
    assert len(calls) == call_count
