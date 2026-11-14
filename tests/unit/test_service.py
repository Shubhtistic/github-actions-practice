from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import pytest

from src.actions.events import service as event_service
from src.actions.events.exceptions import (
    EventNotFoundError,
    InvalidEventTimeError,
)
from src.actions.events.models import Event
from src.actions.events.schemas import EventCreate, EventUpdate

START = datetime(2026, 11, 15, 10, 0, tzinfo=UTC)
END = START + timedelta(hours=2)


@asynccontextmanager
async def _fake_session():
    yield object()


def _event(event_id: int = 1) -> Event:
    return Event(
        id=event_id,
        title="Existing",
        description=None,
        location=None,
        starts_at=START,
        ends_at=END,
        created_at=START,
        updated_at=START,
    )


def _fail_session():
    raise AssertionError("database session should not be opened")


async def test_create_event_creates_model_and_returns_repo_result(monkeypatch):
    captured = {}

    async def fake_create(event, db_session):
        captured["event"] = event
        captured["session"] = db_session
        event.id = 5
        return event

    monkeypatch.setattr(event_service, "get_db_session", _fake_session)
    monkeypatch.setattr(event_service.repo, "create_event", fake_create)

    result = await event_service.EventService.create_event(
        EventCreate(title="Launch", starts_at=START, ends_at=END)
    )

    assert result.id == 5
    assert captured["event"].title == "Launch"
    assert captured["event"].starts_at == START
    assert captured["session"] is not None


async def test_create_event_rejects_invalid_time_before_opening_session(monkeypatch):
    monkeypatch.setattr(event_service, "get_db_session", _fail_session)

    with pytest.raises(InvalidEventTimeError):
        await event_service.EventService.create_event(
            EventCreate(title="Launch", starts_at=END, ends_at=START)
        )


async def test_get_event_returns_found_event(monkeypatch):
    event = _event()

    async def fake_get(event_id, db_session):
        assert event_id == 1
        return event

    monkeypatch.setattr(event_service, "get_db_session", _fake_session)
    monkeypatch.setattr(event_service.repo, "get_event", fake_get)

    assert await event_service.EventService.get_event(1) is event


async def test_get_event_raises_when_missing(monkeypatch):
    async def fake_get(event_id, db_session):
        return None

    monkeypatch.setattr(event_service, "get_db_session", _fake_session)
    monkeypatch.setattr(event_service.repo, "get_event", fake_get)

    with pytest.raises(EventNotFoundError) as exc_info:
        await event_service.EventService.get_event(99)

    assert exc_info.value.event_id == 99


async def test_list_events_forwards_pagination(monkeypatch):
    captured = {}

    async def fake_list(db_session, limit=20, offset=0):
        captured.update(limit=limit, offset=offset)
        return [_event()]

    monkeypatch.setattr(event_service, "get_db_session", _fake_session)
    monkeypatch.setattr(event_service.repo, "list_events", fake_list)

    result = await event_service.EventService.list_events(limit=5, offset=10)

    assert captured == {"limit": 5, "offset": 10}
    assert len(result) == 1


async def test_update_event_applies_only_provided_fields(monkeypatch):
    event = _event()
    captured = {}

    async def fake_get(event_id, db_session):
        return event

    async def fake_update(target, changes, db_session):
        captured["target"] = target
        captured["changes"] = changes
        return target

    monkeypatch.setattr(event_service, "get_db_session", _fake_session)
    monkeypatch.setattr(event_service.repo, "get_event", fake_get)
    monkeypatch.setattr(event_service.repo, "update_event", fake_update)

    result = await event_service.EventService.update_event(
        1, EventUpdate(title="Renamed")
    )

    assert result is event
    assert captured["target"] is event
    assert captured["changes"] == {"title": "Renamed"}


async def test_update_event_validates_merged_times(monkeypatch):
    event = _event()

    async def fake_get(event_id, db_session):
        return event

    async def fake_update(target, changes, db_session):
        raise AssertionError("update should not be persisted")

    monkeypatch.setattr(event_service, "get_db_session", _fake_session)
    monkeypatch.setattr(event_service.repo, "get_event", fake_get)
    monkeypatch.setattr(event_service.repo, "update_event", fake_update)

    with pytest.raises(InvalidEventTimeError):
        await event_service.EventService.update_event(
            1, EventUpdate(ends_at=START - timedelta(minutes=1))
        )


async def test_update_event_raises_when_missing(monkeypatch):
    async def fake_get(event_id, db_session):
        return None

    monkeypatch.setattr(event_service, "get_db_session", _fake_session)
    monkeypatch.setattr(event_service.repo, "get_event", fake_get)

    with pytest.raises(EventNotFoundError):
        await event_service.EventService.update_event(1, EventUpdate(title="x"))


async def test_delete_event_succeeds(monkeypatch):
    captured = {}

    async def fake_delete(event_id, db_session):
        captured["event_id"] = event_id
        return True

    monkeypatch.setattr(event_service, "get_db_session", _fake_session)
    monkeypatch.setattr(event_service.repo, "delete_event", fake_delete)

    assert await event_service.EventService.delete_event(3) is None
    assert captured["event_id"] == 3


async def test_delete_event_raises_when_missing(monkeypatch):
    async def fake_delete(event_id, db_session):
        return False

    monkeypatch.setattr(event_service, "get_db_session", _fake_session)
    monkeypatch.setattr(event_service.repo, "delete_event", fake_delete)

    with pytest.raises(EventNotFoundError):
        await event_service.EventService.delete_event(3)


@pytest.mark.parametrize(
    ("starts_at", "ends_at"),
    [
        (START, START),
        (END, START),
        (START, START - timedelta(seconds=1)),
    ],
)
def test_validate_times_rejects_non_increasing_ranges(starts_at, ends_at):
    with pytest.raises(InvalidEventTimeError):
        event_service.EventService._validate_times(starts_at, ends_at)


def test_validate_times_accepts_increasing_ranges():
    assert event_service.EventService._validate_times(START, END) is None
