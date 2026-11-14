from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from src.actions.events import repo
from src.actions.events.models import Event
from tests.conftest import make_event

START = datetime(2026, 11, 15, 10, 0, tzinfo=UTC)


async def test_create_and_get_event(db_session):
    created = await repo.create_event(make_event(title="Stored"), db_session)

    assert created.id is not None

    fetched = await repo.get_event(created.id, db_session)

    assert fetched is not None
    assert fetched.title == "Stored"


async def test_get_event_returns_none_when_missing(db_session):
    assert await repo.get_event(123_456, db_session) is None


async def test_list_events_orders_by_start_time(db_session):
    await repo.create_event(
        make_event(title="Third", starts_at=START + timedelta(days=3)), db_session
    )
    await repo.create_event(make_event(title="First", starts_at=START), db_session)
    await repo.create_event(
        make_event(title="Second", starts_at=START + timedelta(days=1)), db_session
    )

    events = await repo.list_events(db_session)

    assert [event.title for event in events] == ["First", "Second", "Third"]


async def test_list_events_paginates(db_session):
    for index in range(4):
        await repo.create_event(
            make_event(
                title=f"Event {index}",
                starts_at=START + timedelta(days=index),
            ),
            db_session,
        )

    events = await repo.list_events(db_session, limit=2, offset=1)

    assert [event.title for event in events] == ["Event 1", "Event 2"]


async def test_update_event_applies_changes_and_bumps_timestamp(db_session):
    event = await repo.create_event(make_event(title="Before"), db_session)
    previous_updated_at = event.updated_at

    updated = await repo.update_event(
        event,
        {"title": "After", "location": "Office"},
        db_session,
    )
    await db_session.flush()

    assert updated.title == "After"
    assert updated.location == "Office"
    assert updated.updated_at >= previous_updated_at

    fetched = await db_session.get(Event, event.id)
    assert fetched.title == "After"


async def test_update_event_ignores_unknown_changes(db_session):
    event = await repo.create_event(make_event(title="Before"), db_session)

    await repo.update_event(event, {}, db_session)

    assert event.title == "Before"


async def test_delete_event_reports_whether_row_was_deleted(db_session):
    event = await repo.create_event(make_event(), db_session)

    assert await repo.delete_event(event.id, db_session) is True
    assert await repo.delete_event(event.id, db_session) is False

    remaining = (await db_session.execute(select(Event))).scalars().all()
    assert remaining == []
