"""Pytest configuration for API smoke tests."""

import os
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Dict, Optional

import pytest

# ── Deterministic environment configuration ───────────────────────────────────
TEST_DB_PATH = Path("test_whisper.db")
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ.setdefault("SECRET_KEY", "unit-test-secret-key-should-be-long-and-randomized-1234567890")
os.environ.setdefault("JWT_SECRET_KEY", "unit-test-jwt-secret-key-that-is-also-long-0987654321")
os.environ.setdefault("REDIS_PASSWORD", "unit-test-redis-password")
os.environ.setdefault("ADMIN_BOOTSTRAP_PASSWORD", "super-secure-test-password-!123")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH}")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import api.settings as settings_module  # noqa: E402

settings = settings_module.settings
from api.paths import storage  # noqa: E402
from api.middlewares.session_security import session_security  # noqa: E402

# Enable debug mode for relaxed local security checks during tests.
settings.debug = True
settings.cors_origins = "http://localhost,http://testserver"
if "vite_api_host" not in settings.model_fields_set:
    settings = settings.model_copy(update={"vite_api_host": "http://localhost:8001"})
    settings_module.settings = settings

# Ensure runtime directories exist for tests.
storage.ensure_directories()

# Align session security cookie settings with debug mode overrides.
session_security.cookie_config["secure"] = False
session_security.refresh_cookie_config["secure"] = False
session_security.cookie_config["samesite"] = "lax"
session_security.refresh_cookie_config["samesite"] = "lax"


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db() -> None:
    """Remove the temporary SQLite database after the test session."""
    yield
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(scope="session")
def client() -> "TestClient":
    """Provide a FastAPI test client with application lifespan events."""
    from fastapi.testclient import TestClient
    from api.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def security_headers() -> Callable[[Optional[str], bool], Dict[str, str]]:
    """Return a helper for constructing security-compliant headers."""

    def _build(token: Optional[str] = None, include_placeholder_auth: bool = False) -> Dict[str, str]:
        headers = {
            "Referer": "http://localhost",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "pytest-client",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        elif include_placeholder_auth:
            headers["Authorization"] = "Bearer placeholder-token"
        return headers

    return _build


@pytest.fixture
def admin_token(client, security_headers) -> str:
    """Authenticate using the bootstrap admin credentials and return the JWT."""
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": os.environ["ADMIN_BOOTSTRAP_PASSWORD"]},
        headers=security_headers(include_placeholder_auth=True),
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    return payload["access_token"]


@pytest.fixture(autouse=True)
def stub_job_queue(monkeypatch):
    """Stub the in-process job queue to avoid heavy background work."""
    import api.routes.jobs as jobs_routes

    class StubQueue:
        def __init__(self):
            self.submitted = []
            self.jobs: Dict[str, SimpleNamespace] = {}

        def submit_job(self, task_name: str, **kwargs) -> str:
            job_id = kwargs.get("job_id") or f"job-{len(self.submitted)}"
            record = {"task_name": task_name, "kwargs": kwargs, "job_id": job_id}
            self.submitted.append(record)
            self.jobs[job_id] = SimpleNamespace(state="PENDING")
            return job_id

        def get_job(self, job_id: str) -> Optional[SimpleNamespace]:
            return self.jobs.get(job_id)

    stub = StubQueue()
    monkeypatch.setattr(jobs_routes, "job_queue", stub)
    yield stub

