from api.routes import auth
from api.services.users import create_user
from jose import jwt
from api.settings import settings


def test_register_and_token(client):
    client.app.dependency_overrides.clear()
    resp = client.post("/register", data={"username": "alice", "password": "pw"})
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert payload["role"] == "user"

    resp = client.post("/token", data={"username": "alice", "password": "pw"})
    assert resp.status_code == 200
    token2 = resp.json()["access_token"]
    payload2 = jwt.decode(token2, settings.secret_key, algorithms=[settings.algorithm])
    assert payload2["role"] == "user"


def test_protected_endpoint_requires_auth(client):
    client.app.dependency_overrides.clear()
    resp = client.get("/metrics")
    assert resp.status_code == 401

    client.post("/register", data={"username": "bob", "password": "pw"})
    token = client.post("/token", data={"username": "bob", "password": "pw"}).json()[
        "access_token"
    ]
    resp = client.get("/metrics", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403

    create_user("admin", "pw", role="admin")
    admin_token = client.post(
        "/token", data={"username": "admin", "password": "pw"}
    ).json()["access_token"]
    resp = client.get("/metrics", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
