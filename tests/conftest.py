import asyncio
from collections.abc import AsyncGenerator, AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from src.actions.events import service as event_service
from src.actions.events.models import Event
from src.actions.infrastructure.config import get_settings

# Importing the model registers its table on SQLModel.metadata.
_ = Event

_settings = get_settings()
_base_url = make_url(_settings.postgres.postgres_async_url)
_admin_url = _base_url.set(database="postgres")
TEST_DATABASE = f"{_base_url.database}_test"
_test_url = _base_url.set(database=TEST_DATABASE)


async def _create_database_if_missing() -> None:
    admin_engine = create_async_engine(
        _admin_url,
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )
    try:
        async with admin_engine.connect() as connection:
            exists = await connection.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": TEST_DATABASE},
            )
            if not exists:
                await connection.execute(text(f'CREATE DATABASE "{TEST_DATABASE}"'))
    finally:
        await admin_engine.dispose()


async def _reset_schema() -> None:
    test_engine = create_async_engine(_test_url, poolclass=NullPool)
    try:
        async with test_engine.begin() as connection:
            await connection.run_sync(SQLModel.metadata.drop_all)
            await connection.run_sync(SQLModel.metadata.create_all)
    finally:
        await test_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _prepare_test_database() -> None:
    """Create the dedicated test database and start with an empty schema."""
    asyncio.run(_create_database_if_missing())
    asyncio.run(_reset_schema())


@pytest_asyncio.fixture
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """Postgres engine pointed at the isolated test database."""
    test_engine = create_async_engine(_test_url, poolclass=NullPool)
    async with test_engine.begin() as connection:
        await connection.execute(
            text('TRUNCATE TABLE "events" RESTART IDENTITY CASCADE')
        )

    yield test_engine

    await test_engine.dispose()


@pytest_asyncio.fixture
async def session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


def _session_context(
    session_factory: async_sessionmaker[AsyncSession],
) -> Callable:
    """Mirror the production session/transaction boundary."""

    @asynccontextmanager
    async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as db_session:
            try:
                async with db_session.begin():
                    yield db_session
            except Exception:
                if db_session.in_transaction():
                    await db_session.rollback()
                raise

    return get_db_session


@pytest.fixture
def use_test_db(
    monkeypatch: pytest.MonkeyPatch,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Point the event service at the isolated Postgres test database."""
    monkeypatch.setattr(
        event_service,
        "get_db_session",
        _session_context(session_factory),
    )


def make_event(**overrides) -> Event:
    starts_at = overrides.pop("starts_at", datetime.now(UTC) + timedelta(days=1))
    ends_at = overrides.pop("ends_at", starts_at + timedelta(hours=2))
    defaults = {
        "title": "Release party",
        "description": "Ship it",
        "location": "Remote",
        "starts_at": starts_at,
        "ends_at": ends_at,
    }
    defaults.update(overrides)
    return Event(**defaults)
