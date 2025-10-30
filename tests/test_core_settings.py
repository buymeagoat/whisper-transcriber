"""Tests for the core application settings helpers."""

from api.core.settings import CoreSettings


def test_database_dsn_prefers_database_url(monkeypatch):
    """An explicit DATABASE_URL should be returned unchanged."""

    monkeypatch.setenv("DATABASE_URL", "postgresql://app:secret@pg.example.com/prod")
    settings = CoreSettings()

    assert settings.database_dsn() == "postgresql://app:secret@pg.example.com/prod"
    assert settings.database_url == "postgresql://app:secret@pg.example.com/prod"


def test_database_dsn_composed_from_postgres_components(monkeypatch):
    """Component configuration should build a properly quoted PostgreSQL DSN."""

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_HOST", "pg.internal")
    monkeypatch.setenv("POSTGRES_PORT", "5433")
    monkeypatch.setenv("POSTGRES_DB", "service")
    monkeypatch.setenv("POSTGRES_USER", "whisper-app")
    monkeypatch.setenv("POSTGRES_PASSWORD", "s3cr3t! with spaces")
    monkeypatch.setenv("POSTGRES_SSLMODE", "require")
    monkeypatch.setenv("POSTGRES_OPTIONS", "-c statement_timeout=5000")

    settings = CoreSettings()

    assert (
        settings.database_dsn()
        == "postgresql://whisper-app:s3cr3t%21+with+spaces@pg.internal:5433/service?sslmode=require&options=-c+statement_timeout%3D5000"
    )
