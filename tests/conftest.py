"""
Test configuration and fixtures for Whisper Transcriber
Ensures proper environment setup and provides common test utilities.
"""

import os
import sys
from pathlib import Path

# CRITICAL: Set up environment variables BEFORE any other imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set test environment variables first
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("LOG_LEVEL", "ERROR")

# Ensure required secrets are available for testing BEFORE loading .env
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-32-chars-long")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-for-testing-32-chars")
os.environ.setdefault("REDIS_PASSWORD", "test-redis-password")
os.environ.setdefault("DATABASE_ENCRYPTION_KEY", "test-db-encryption-key-32-chars-long")
os.environ.setdefault("ADMIN_API_KEY", "test-admin-api-key-24-chars")
os.environ.setdefault("CELERY_SECRET_KEY", "test-celery-secret-key-32-chars-long")

# Disable security validation for tests
os.environ["ENFORCE_SECURITY_VALIDATION"] = "false"

# Configure test database
TEST_DB_PATH = PROJECT_ROOT / "test_database.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

# Configure test Redis (use fake redis for testing)
os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # Use test database 15
os.environ["CELERY_BROKER_URL"] = "memory://"  # Use in-memory broker for tests

# NOW load environment variables from .env (will not override existing)
from dotenv import load_dotenv
test_env_path = PROJECT_ROOT / ".env"
if test_env_path.exists():
    load_dotenv(test_env_path, override=False)  # Don't override test values

# NOW safe to import other modules
import pytest
import tempfile
from unittest.mock import Mock, patch
from typing import Generator, Dict, Any

# Import application modules AFTER environment setup
try:
    from api.main import app
    from api.settings import settings
    from api.models import Base
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create test database engine
    test_engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
except ImportError as e:
    print(f"Warning: Could not import application modules: {e}")
    app = None
    settings = None


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment before running any tests."""
    # Create test directories
    test_dirs = [
        PROJECT_ROOT / "test_uploads",
        PROJECT_ROOT / "test_transcripts", 
        PROJECT_ROOT / "test_models",
        PROJECT_ROOT / "test_cache"
    ]
    
    for test_dir in test_dirs:
        test_dir.mkdir(exist_ok=True)
    
    # Set up test environment variables pointing to test directories
    os.environ["UPLOAD_DIR"] = str(PROJECT_ROOT / "test_uploads")
    os.environ["TRANSCRIPTS_DIR"] = str(PROJECT_ROOT / "test_transcripts")
    os.environ["MODELS_DIR"] = str(PROJECT_ROOT / "test_models")
    os.environ["CACHE_DIR"] = str(PROJECT_ROOT / "test_cache")
    
    yield
    
    # Cleanup after all tests
    import shutil
    for test_dir in test_dirs:
        if test_dir.exists():
            shutil.rmtree(test_dir, ignore_errors=True)
    
    # Clean up test database
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(scope="function")
def test_database():
    """Create a fresh test database for each test."""
    if not app:
        pytest.skip("Application not available")
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create a test session
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def test_client():
    """Create a test client for API testing."""
    if not app:
        pytest.skip("Application not available")
    
    from fastapi.testclient import TestClient
    
    # Create test database tables
    Base.metadata.create_all(bind=test_engine)
    
    with TestClient(app) as client:
        yield client
    
    # Cleanup
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def authenticated_client(test_client):
    """Create an authenticated test client."""
    if not test_client:
        pytest.skip("Test client not available")
    
    # Create test user and get token
    user_data = {
        "username": "testuser",
        "password": "testpassword123",
        "email": "test@example.com"
    }
    
    # Register user
    response = test_client.post("/auth/register", json=user_data)
    if response.status_code not in [200, 201]:
        # Try login instead (user might already exist)
        response = test_client.post("/auth/login", json={
            "username": user_data["username"],
            "password": user_data["password"]
        })
    
    if response.status_code in [200, 201]:
        token = response.json().get("access_token")
        if token:
            test_client.headers.update({"Authorization": f"Bearer {token}"})
    
    yield test_client


@pytest.fixture(scope="function")
def temp_audio_file():
    """Create a temporary audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        # Create a minimal WAV file header (44 bytes)
        wav_header = (
            b'RIFF'
            b'\x24\x00\x00\x00'  # File size (36 bytes)
            b'WAVE'
            b'fmt '
            b'\x10\x00\x00\x00'  # Format chunk size (16 bytes)
            b'\x01\x00'          # Audio format (PCM)
            b'\x01\x00'          # Number of channels (1)
            b'\x44\xAC\x00\x00'  # Sample rate (44100)
            b'\x88\x58\x01\x00'  # Byte rate
            b'\x02\x00'          # Block align
            b'\x10\x00'          # Bits per sample (16)
            b'data'
            b'\x00\x00\x00\x00'  # Data chunk size (0 - no audio data)
        )
        temp_file.write(wav_header)
        temp_file_path = temp_file.name
    
    yield temp_file_path
    
    # Cleanup
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)


@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis for tests that don't need real Redis."""
    mock_redis = Mock()
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.exists.return_value = False
    
    with patch('redis.Redis', return_value=mock_redis):
        yield mock_redis


@pytest.fixture(scope="function")
def mock_celery():
    """Mock Celery for tests that don't need real task processing."""
    mock_task = Mock()
    mock_task.id = "test-task-id"
    mock_task.state = "SUCCESS"
    mock_task.result = {"status": "completed"}
    
    mock_celery = Mock()
    mock_celery.send_task.return_value = mock_task
    
    with patch('celery.Celery', return_value=mock_celery):
        yield mock_celery


@pytest.fixture(scope="function")
def mock_whisper():
    """Mock Whisper model for tests that don't need real transcription."""
    mock_model = Mock()
    mock_model.transcribe.return_value = {
        "text": "This is a test transcription.",
        "segments": [
            {
                "start": 0.0,
                "end": 3.0,
                "text": "This is a test transcription."
            }
        ]
    }
    
    with patch('whisper.load_model', return_value=mock_model):
        yield mock_model


@pytest.fixture(scope="function")
def sample_transcript_data() -> Dict[str, Any]:
    """Provide sample transcript data for testing."""
    return {
        "text": "This is a sample transcript for testing purposes.",
        "language": "en",
        "segments": [
            {
                "start": 0.0,
                "end": 2.5,
                "text": "This is a sample transcript"
            },
            {
                "start": 2.5,
                "end": 5.0,
                "text": "for testing purposes."
            }
        ],
        "metadata": {
            "model": "small",
            "duration": 5.0,
            "confidence": 0.95
        }
    }


# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


def pytest_configure(config):
    """Configure pytest settings."""
    # Register custom markers
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication related"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add asyncio marker to async tests
        if "async" in item.name or "asyncio" in str(item.function):
            item.add_marker(pytest.mark.asyncio)
        
        # Add slow marker to tests that typically take longer
        if any(keyword in item.name.lower() for keyword in ["integration", "end_to_end", "performance"]):
            item.add_marker(pytest.mark.slow)


# Skip tests that require missing modules
def pytest_runtest_setup(item):
    """Setup hook to skip tests with missing dependencies."""
    # For now, just continue - we'll handle import errors in individual tests
    pass


# Utility functions for tests
def create_test_user(db_session, username: str = "testuser", password: str = "testpass123"):
    """Helper function to create a test user."""
    try:
        from api.services.user_service import UserService
        user_service = UserService()
        return user_service.create_user(
            username=username,
            password=password,
            email=f"{username}@test.com",
            db=db_session
        )
    except ImportError:
        return None


def get_test_file_path(filename: str) -> Path:
    """Get path to test file in the test fixtures directory."""
    test_files_dir = PROJECT_ROOT / "tests" / "fixtures"
    test_files_dir.mkdir(exist_ok=True)
    return test_files_dir / filename