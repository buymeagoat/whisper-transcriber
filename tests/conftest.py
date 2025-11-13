"""Pytest configuration for asynchronous API integration tests."""

from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
from contextlib import suppress
from importlib import reload
from pathlib import Path
from types import SimpleNamespace
from typing import AsyncIterator, Callable, Dict, Iterator, Optional

import pytest
import pytest_asyncio
from contextlib import AsyncExitStack

from httpx import ASGITransport, AsyncClient
from fastapi.testclient import TestClient

# ── Ephemeral filesystem layout ─────────────────────────────────────────────────
TEST_ROOT = Path(tempfile.mkdtemp(prefix="whisper-tests-"))
TEST_DB_PATH = TEST_ROOT / "test.db"
UPLOAD_DIR = TEST_ROOT / "uploads"
TRANSCRIPTS_DIR = TEST_ROOT / "transcripts"
CACHE_DIR = TEST_ROOT / "cache"
MODELS_DIR = TEST_ROOT / "models"
LOGS_DIR = TEST_ROOT / "logs"

for directory in (UPLOAD_DIR, TRANSCRIPTS_DIR, CACHE_DIR, MODELS_DIR, LOGS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# ── Deterministic environment configuration ─────────────────────────────────────
os.environ.setdefault("SECRET_KEY", "unit-test-secret-key-should-be-long-and-randomized-1234567890")
os.environ.setdefault("JWT_SECRET_KEY", "unit-test-jwt-secret-key-that-is-also-long-0987654321")
os.environ.setdefault("REDIS_PASSWORD", "unit-test-redis-password")
os.environ.setdefault("ADMIN_BOOTSTRAP_PASSWORD", "super-secure-test-password-!123")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH}")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")

# Settings must be configured after environment variables are in place.
import api.settings as settings_module  # noqa: E402

settings = settings_module.settings.model_copy(
    update={
        "debug": True,
        "cors_origins": "http://localhost,http://testserver",
        "vite_api_host": "http://localhost:8001",
        "database_url": os.environ["DATABASE_URL"],
        "db_url": os.environ["DATABASE_URL"],
        "redis_url": os.environ["REDIS_URL"],
        "celery_broker_url": os.environ["CELERY_BROKER_URL"],
        "celery_result_backend": os.environ["CELERY_RESULT_BACKEND"],
        "upload_dir": UPLOAD_DIR,
        "transcripts_dir": TRANSCRIPTS_DIR,
        "cache_dir": CACHE_DIR,
        "models_dir": MODELS_DIR,
    }
)
settings_module.settings = settings

# Reload path helpers so they pick up the updated settings.
import api.paths as paths_module  # noqa: E402

paths_module = reload(paths_module)
storage = paths_module.storage
storage.ensure_directories()

# Align session security with relaxed local settings.
from api.middlewares.session_security import session_security  # noqa: E402

session_security.cookie_config["secure"] = False
session_security.refresh_cookie_config["secure"] = False
session_security.cookie_config["samesite"] = "lax"
session_security.refresh_cookie_config["samesite"] = "lax"

# Re-initialise ORM so that the engine points to the temporary database.
import api.orm_bootstrap as orm_bootstrap_module  # noqa: E402

orm_bootstrap = reload(orm_bootstrap_module)
import api.security.audit_models as audit_models  # noqa: E402
import api.models as models_module  # noqa: E402
from sqlalchemy.orm import Session

from api.services.user_service import UserService  # noqa: E402

reload(audit_models)
reload(models_module)
orm_bootstrap.validate_or_initialize_database()
SessionLocal = orm_bootstrap.SessionLocal


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_artifacts() -> Iterator[None]:
    """Remove the ephemeral database and storage directories after the test run."""

    yield
    with suppress(FileNotFoundError):
        TEST_DB_PATH.unlink()
    shutil.rmtree(TEST_ROOT, ignore_errors=True)


@pytest.fixture(scope="session")
def event_loop():
    """Provide a dedicated asyncio event loop for the entire test session."""

    loop = asyncio.new_event_loop()
    yield loop
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def fakeredis_server() -> AsyncIterator[None]:
    """Back Redis integrations with an in-memory fakeredis instance."""

    import fakeredis.aioredis as fredis
    import redis.asyncio as redis_async

    fake_server = fredis.FakeServer()  # type: ignore[attr-defined]

    def _create_client() -> fredis.FakeRedis:
        client = fredis.FakeRedis(server=fake_server, decode_responses=True)

        async def _config_set(*args, **kwargs):  # type: ignore[override]
            return True

        client.config_set = _config_set  # type: ignore[assignment]
        return client

    patcher = pytest.MonkeyPatch()
    patcher.setattr(redis_async, "from_url", lambda *args, **kwargs: _create_client())
    patcher.setattr(redis_async, "Redis", fredis.FakeRedis)

    yield

    client = fredis.FakeRedis(server=fake_server, decode_responses=True)
    await client.flushall()
    await client.close()
    patcher.undo()


@pytest.fixture(scope="session")
def app():
    """Import the FastAPI application once for all tests."""

    from api.main import app as fastapi_app

    return fastapi_app


@pytest_asyncio.fixture
async def async_client(app):
    """Provide an HTTPX asynchronous client wired to the FastAPI app."""

    transport = ASGITransport(app=app)
    async with AsyncExitStack() as stack:
        lifespan_cm = app.router.lifespan_context
        if lifespan_cm is not None:
            await stack.enter_async_context(lifespan_cm(app))
        else:
            await app.router.startup()
            stack.push_async_callback(app.router.shutdown)
        client = AsyncClient(transport=transport, base_url="http://testserver")
        await stack.enter_async_context(client)
        yield client


@pytest.fixture
def client(app):
    """Provide a synchronous TestClient for legacy tests."""

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def security_headers() -> Callable[..., Dict[str, str]]:
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
def db_session() -> Iterator[Session]:
    """Provide a database session bound to the ephemeral SQLite database."""

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def standard_user_credentials(db_session) -> tuple[str, str]:
    """Ensure a regular test user exists and return its credentials."""

    username = "testuser"
    password = "Password123!"
    service = UserService()
    user = db_session.query(models_module.User).filter_by(username=username).first()
    if user is None:
        service.create_user(db_session, username, password)
        db_session.commit()
    return username, password


@pytest.fixture
def test_user(db_session, standard_user_credentials) -> models_module.User:
    """Return the standard test user instance."""

    username, _ = standard_user_credentials
    user = db_session.query(models_module.User).filter_by(username=username).first()
    assert user is not None
    return user


@pytest.fixture
def auth_headers(
    client: TestClient,
    security_headers: Callable[..., Dict[str, str]],
    standard_user_credentials: tuple[str, str],
) -> Dict[str, str]:
    """Authenticate as a regular user and return authorization headers."""

    username, password = standard_user_credentials
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
        headers=security_headers(token=None, include_placeholder_auth=True),
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return security_headers(token=token, include_placeholder_auth=False)


@pytest.fixture
def admin_headers(
    admin_token: str,
    security_headers: Callable[..., Dict[str, str]],
) -> Dict[str, str]:
    """Return authorization headers for the bootstrap admin user."""

    return security_headers(token=admin_token, include_placeholder_auth=False)


@pytest_asyncio.fixture
async def admin_token(async_client: AsyncClient, security_headers) -> str:
    """Authenticate using the bootstrap admin credentials and return the JWT."""

    response = await async_client.post(
        "/auth/login",
        json={"username": "admin", "password": os.environ["ADMIN_BOOTSTRAP_PASSWORD"]},
        headers=security_headers(include_placeholder_auth=True),
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    return payload["access_token"]


@pytest.fixture
def stub_job_queue(monkeypatch):
    """Stub the Celery-backed job queue to avoid hitting a real broker."""

    class StubQueue:
        def __init__(self):
            self.submitted: list[Dict[str, object]] = []
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
    import importlib

    job_queue_module = importlib.import_module("api.services.job_queue")
    jobs_routes = importlib.import_module("api.routes.jobs")
    admin_routes = importlib.import_module("api.routes.admin")

    monkeypatch.setattr(job_queue_module, "job_queue", stub, raising=False)
    monkeypatch.setattr(jobs_routes, "job_queue", stub, raising=False)
    monkeypatch.setattr(admin_routes, "job_queue", stub, raising=False)
    return stub
