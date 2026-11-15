from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.actions.infrastructure.config import get_settings

# --- settings ---
settings = get_settings()


# --- Engine ----
db_engine = create_async_engine(
    settings.postgres.postgres_async_url,
    echo=False,
    pool_size=10,
    max_overflow=10,
    pool_timeout=20,
    pool_recycle=1800,
    pool_pre_ping=True,
)


# --- session factory ----
SessionFactory = async_sessionmaker(
    bind=db_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# --- transaction context ---
@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """Open one session and transaction for an application operation.

    Usable directly as a FastAPI dependency; commits on success and
    rolls back on any exception.
    """
    async with SessionFactory() as db_session:
        try:
            async with db_session.begin():
                yield db_session
        except Exception:
            if db_session.in_transaction():
                await db_session.rollback()
            raise
