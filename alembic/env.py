import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Attempt to import project metadata; fall back to None to keep scaffold safe.
target_metadata = None
try:
    # try common locations
    from backend.database import metadata as db_metadata
    target_metadata = db_metadata
except Exception:
    try:
        from backend.models import metadata as models_metadata
        target_metadata = models_metadata
    except Exception:
        target_metadata = None


def get_url():
    # Prefer direct DATABASE_URL env var; otherwise, try alembic.ini substitution
    return os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URL') or config.get_main_option('sqlalchemy.url')


def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
