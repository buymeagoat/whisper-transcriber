import pytest

from api import orm_bootstrap


def test_missing_alembic_raises_runtime_error(temp_db, monkeypatch):
    def raise_fn(*a, **k):
        raise FileNotFoundError()

    monkeypatch.setattr(orm_bootstrap.subprocess, "run", raise_fn)

    with pytest.raises(RuntimeError, match="Alembic not installed"):
        orm_bootstrap.validate_or_initialize_database()
