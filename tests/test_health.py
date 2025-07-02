import importlib
from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.main as main


def test_health_db_failure(monkeypatch):
    def bad_session():
        class Dummy:
            def __enter__(self):
                raise Exception("boom")

            def __exit__(self, exc_type, exc, tb):
                pass

        return Dummy()

    monkeypatch.setattr(main, "SessionLocal", bad_session)

    app = FastAPI()
    app.add_api_route("/health", main.health_check, methods=["GET"])

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 500
    data = resp.json()
    assert data["status"] == "db_error"
    assert "boom" in data["detail"]
