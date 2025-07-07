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
