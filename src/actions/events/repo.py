from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.actions.events.models import Event
from src.actions.infrastructure.repo_helpers import (
    create,
    delete_by_id,
    get_all,
    get_one,
)

# --- Event repo: thin data access layer over the generic repo helpers ---


async def create_event(
    event: Event,
    db_session: AsyncSession,
) -> Event:
    """Insert a new event row and flush it; the request transaction commits."""
    return await create(event, db_session)


async def get_event(
    event_id: int,
    db_session: AsyncSession,
) -> Event | None:
    """Fetch a single event by primary key."""
    return await get_one(Event, event_id, db_session)


async def list_events(
    db_session: AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> list[Event]:
    """Fetch a page of events ordered by start time."""
    event_table = cast(Any, Event).__table__
    stmt: Select[Event] = (
        select(Event).order_by(event_table.c.starts_at).offset(offset).limit(limit)
    )
    return list(await get_all(stmt, db_session))


async def update_event(
    event: Event,
    changes: dict,
    db_session: AsyncSession,
) -> Event:
    """Apply a dict of validated changes to a loaded event and flush."""
    for key, value in changes.items():
        setattr(event, key, value)
    event.updated_at = datetime.now(UTC)
    await db_session.flush()
    return event


async def delete_event(
    event_id: int,
    db_session: AsyncSession,
) -> bool:
    """Delete an event by primary key. Returns True if a row was deleted."""
    return await delete_by_id(Event, event_id, db_session)
