from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy.exc import OperationalError
from alembic import context

# Alembic Config object
config = context.config

# Setup loggers if a config file is present
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

import os

from api.settings import settings

db_url = os.getenv("DB_URL") or settings.db_url
if not db_url:
    raise SystemExit("DB_URL is not set and no default available from settings")

config.set_main_option("sqlalchemy.url", db_url)

# === PATCH: enable autogeneration by pointing to SQLAlchemy metadata
from api.models import Base

target_metadata = Base.metadata

# Other Alembic options
# my_important_option = config.get_main_option("my_important_option")
# ...


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode without a live DB connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with DB connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
            )

            with context.begin_transaction():
                context.run_migrations()
    except OperationalError as exc:
        raise SystemExit(
            "Database unreachable. Ensure a PostgreSQL service is running and DB_URL is correct."
            f" Last error: {exc}"
        )


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
