from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from src.actions.events import service as event_service
from src.actions.events.models import Event

# Importing the model registers its table on SQLModel.metadata.
_ = Event


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    """Isolated in-memory SQLite engine with all tables created."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with test_engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)

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
    async def get_db_session() -> AsyncIterator[AsyncSession]:
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
    """Point the event service at the isolated SQLite database."""
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
