"""
alembic/env.py
--------------
Alembic environment configuration for LEARNABLE / SAIS.
Reads DATABASE_URL from the application's Settings so it honours .env.
Imports all SQLAlchemy models so autogenerate can detect schema changes.
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# ── Make the `backend/` package importable ────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings  # noqa: E402  (import after sys.path patch)
from app.core.database import Base    # noqa: E402

# Import all models so Alembic's autogenerate picks them up
import app.models.user            # noqa: F401
import app.models.course          # noqa: F401
import app.models.timetable       # noqa: F401
import app.models.task            # noqa: F401
import app.models.note            # noqa: F401
import app.models.academic        # noqa: F401
import app.models.study_session   # noqa: F401

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config

# Inject the DATABASE_URL from pydantic-settings into alembic config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Setup Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate support
target_metadata = Base.metadata


# ── Offline migrations (generates SQL script without connecting) ──────────────
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online migrations (connects to DB and applies changes) ────────────────────
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
