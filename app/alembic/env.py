import os
from logging.config import fileConfig
from sqlalchemy import create_engine
from alembic import context
from sqlalchemy import  pool
# --------------------------
# Add the app directory to Python path
# --------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.core.config import settings
from app.db.base import Base
import app.models  # noqa: F401 - registers platform models on Base.metadata
from app.core.domains import import_domain_models

import_domain_models()

# --- START OF OUR CUSTOM CODE ---


# Set the DATABASE_URL environment variable so that alembic.ini can read it
# print(">>> settings.DATABASE_URL =", settings.DATABASE_URL)

os.environ['DATABASE_URL'] = str(settings.DATABASE_URL)
# --- END OF OUR CUSTOM CODE ---


# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- START OF OUR CUSTOM CODE (MODIFICATION) ---
# Tell Alembic what SQLAlchemy models to look at
target_metadata = Base.metadata
# --- END OF OUR CUSTOM CODE (MODIFICATION) ---


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode.'"""
    connectable = create_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
