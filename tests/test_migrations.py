"""Regression tests covering Alembic migration generation."""

import io
from contextlib import redirect_stdout

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.engine import mock as sqlalchemy_mock


@pytest.fixture(autouse=True)
def _allow_mock_connection_keywords(monkeypatch):
    """Permit MockConnection.execute to receive keyword parameters."""

    original_execute = sqlalchemy_mock.MockConnection.execute

    def _execute(self, obj, parameters=None, execution_options=None, **kw):
        if kw:
            if parameters is None:
                parameters = kw
            elif isinstance(parameters, dict):
                parameters = {**parameters, **kw}
            else:
                raise TypeError(
                    "MockConnection.execute received unsupported positional parameters and keyword arguments"
                )
        return original_execute(self, obj, parameters, execution_options)

    monkeypatch.setattr(sqlalchemy_mock.MockConnection, "execute", _execute)


def _make_alembic_config() -> Config:
    """Return an Alembic configuration bound to the local migration scripts."""

    config = Config("alembic.ini")
    config.set_main_option("script_location", "api/migrations")
    config.set_main_option(
        "sqlalchemy.url",
        "postgresql://migration_tester:placeholder@localhost:5432/whisper_transcriber",
    )
    return config


def test_migrations_generate_upgrade_sql_offline():
    """Upgrading to head in offline mode should yield SQL statements."""

    config = _make_alembic_config()

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        command.upgrade(config, "head", sql=True)

    upgrade_sql = buffer.getvalue().strip()
    assert upgrade_sql, "Expected offline upgrade to emit SQL statements"


def test_migrations_generate_downgrade_sql_offline():
    """Downgrading to base in offline mode should yield SQL statements."""

    config = _make_alembic_config()
    head_revision = ScriptDirectory.from_config(config).get_current_head()

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        command.downgrade(config, f"{head_revision}:base", sql=True)

    downgrade_sql = buffer.getvalue().strip()
    assert downgrade_sql, "Expected offline downgrade to emit SQL statements"
