import importlib
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.middlewares.access_log as access_log


def test_log_write_error(monkeypatch):
    importlib.reload(access_log)

    orig_open = Path.open

    def fail_open(self, *args, **kwargs):
        if self == access_log.ACCESS_LOG:
            raise OSError("disk full")
        return orig_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_open)
    warnings = []
    monkeypatch.setattr(
        access_log.backend_log, "warning", lambda msg: warnings.append(msg)
    )

    app = FastAPI()
    app.middleware("http")(access_log.access_logger)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(app)
    resp = client.get("/ping")
    assert resp.status_code == 200
    assert warnings, "logger.warning should be called"
