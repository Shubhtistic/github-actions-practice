import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

from alembic import context
from src.actions.events.models import Event  # noqa: F401 (registers SQLModel table)
from src.actions.infrastructure.config import get_settings

# --- alembic Config object ---
config = context.config

# --- logging ---
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- resolve the async url from project settings ---
config.set_main_option(
    "sqlalchemy.url",
    get_settings().postgres.postgres_async_url,
)

# --- metadata: all models registered via model import ---
target_metadata = SQLModel.metadata


# --- offline mode: emit sql to stdout instead of hitting the db ---
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


# --- online mode: run migrations on a live connection ---
def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
