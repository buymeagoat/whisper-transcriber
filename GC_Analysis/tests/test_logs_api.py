import api.routes.logs as logs


def test_log_event_invalid_json(client):
    resp = client.post(
        "/log_event",
        data="{bad json}",
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "error"


def test_log_path_traversal_blocked(client):
    resp = client.get("/logs/%2e%2e%2Fsecret.txt")
    assert resp.status_code == 404


def test_job_log_requires_auth(client):
    overrides = client.app.dependency_overrides.copy()
    client.app.dependency_overrides.clear()
    resp = client.get("/log/someid")
    assert resp.status_code == 401
    client.app.dependency_overrides.update(overrides)


def test_access_log_requires_auth(client):
    overrides = client.app.dependency_overrides.copy()
    client.app.dependency_overrides.clear()
    resp = client.get("/logs/access")
    assert resp.status_code == 401
    client.app.dependency_overrides.update(overrides)


def test_log_file_requires_auth(client):
    overrides = client.app.dependency_overrides.copy()
    client.app.dependency_overrides.clear()
    resp = client.get("/logs/valid.log")
    assert resp.status_code == 401
    client.app.dependency_overrides.update(overrides)
