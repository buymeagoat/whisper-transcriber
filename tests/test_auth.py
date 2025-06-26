from api.routes import auth


def test_register_and_token(client):
    client.app.dependency_overrides.clear()
    resp = client.post("/register", data={"username": "alice", "password": "pw"})
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    assert token

    resp = client.post("/token", data={"username": "alice", "password": "pw"})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_protected_endpoint_requires_auth(client):
    client.app.dependency_overrides.clear()
    resp = client.get("/metrics")
    assert resp.status_code == 401

    client.post("/register", data={"username": "bob", "password": "pw"})
    token = client.post("/token", data={"username": "bob", "password": "pw"}).json()[
        "access_token"
    ]
    resp = client.get("/metrics", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
