from datetime import UTC, datetime, timedelta

import pytest

from src.actions.events.exceptions import (
    EventNotFoundError,
    InvalidEventTimeError,
)
from src.actions.events.schemas import EventCreate, EventUpdate
from src.actions.events.service import EventService

START = datetime(2026, 11, 15, 10, 0, tzinfo=UTC)
END = START + timedelta(hours=2)

pytestmark = pytest.mark.usefixtures("use_test_db")


def _payload(**overrides) -> EventCreate:
    values = {
        "title": "Launch",
        "description": "Ship it",
        "location": "Remote",
        "starts_at": START,
        "ends_at": END,
    }
    values.update(overrides)
    return EventCreate(**values)


async def test_create_event_persists_and_returns_model():
    event = await EventService.create_event(_payload())

    assert event.id is not None
    assert event.title == "Launch"

    fetched = await EventService.get_event(event.id)
    assert fetched.id == event.id
    assert fetched.description == "Ship it"


async def test_create_event_rejects_invalid_time_range():
    with pytest.raises(InvalidEventTimeError):
        await EventService.create_event(_payload(starts_at=END, ends_at=START))

    assert await EventService.list_events() == []


async def test_get_event_raises_for_unknown_id():
    with pytest.raises(EventNotFoundError):
        await EventService.get_event(4242)


async def test_list_events_returns_ordered_page():
    for index in range(3):
        await EventService.create_event(
            _payload(
                title=f"Event {index}",
                starts_at=START + timedelta(days=index),
                ends_at=START + timedelta(days=index, hours=1),
            )
        )

    events = await EventService.list_events(limit=2, offset=1)

    assert [event.title for event in events] == ["Event 1", "Event 2"]


async def test_update_event_changes_provided_fields_only():
    event = await EventService.create_event(_payload())

    updated = await EventService.update_event(event.id, EventUpdate(title="Renamed"))

    assert updated.id == event.id
    assert updated.title == "Renamed"
    assert updated.description == "Ship it"
    assert updated.location == "Remote"


async def test_update_event_can_move_time_range():
    event = await EventService.create_event(_payload())

    new_start = START + timedelta(days=5)
    updated = await EventService.update_event(
        event.id,
        EventUpdate(starts_at=new_start, ends_at=new_start + timedelta(hours=3)),
    )

    assert updated.starts_at == new_start
    assert updated.ends_at == new_start + timedelta(hours=3)


async def test_update_event_rejects_invalid_merged_range():
    event = await EventService.create_event(_payload())

    with pytest.raises(InvalidEventTimeError):
        await EventService.update_event(
            event.id, EventUpdate(ends_at=START - timedelta(minutes=1))
        )

    fetched = await EventService.get_event(event.id)
    assert fetched.ends_at == END


async def test_update_event_raises_for_unknown_id():
    with pytest.raises(EventNotFoundError):
        await EventService.update_event(999, EventUpdate(title="x"))


async def test_delete_event_removes_row():
    event = await EventService.create_event(_payload())

    await EventService.delete_event(event.id)

    with pytest.raises(EventNotFoundError):
        await EventService.get_event(event.id)


async def test_delete_event_raises_for_unknown_id():
    with pytest.raises(EventNotFoundError):
        await EventService.delete_event(999)
