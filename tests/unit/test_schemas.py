from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from src.actions.events.models import Event
from src.actions.events.schemas import EventCreate, EventRead, EventUpdate

START = datetime(2026, 11, 15, 10, 0, tzinfo=UTC)
END = START + timedelta(hours=2)


def test_event_create_accepts_valid_payload():
    payload = EventCreate(
        title="Launch",
        description="Go live",
        location="Berlin",
        starts_at=START,
        ends_at=END,
    )

    assert payload.title == "Launch"
    assert payload.starts_at == START
    assert payload.ends_at == END


def test_event_create_allows_optional_fields_to_be_omitted():
    payload = EventCreate(title="Launch", starts_at=START, ends_at=END)

    assert payload.description is None
    assert payload.location is None


def test_event_create_requires_title_and_times():
    with pytest.raises(ValidationError) as exc_info:
        EventCreate.model_validate({"title": "Launch", "description": "missing times"})

    errors = {error["loc"][0] for error in exc_info.value.errors()}
    assert errors == {"starts_at", "ends_at"}


@pytest.mark.parametrize("field", ["title", "description", "location"])
@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_event_create_rejects_blank_text(field, value):
    payload = {
        "title": "Launch",
        "starts_at": START,
        "ends_at": END,
        field: value,
    }

    with pytest.raises(ValidationError) as exc_info:
        EventCreate.model_validate(payload)

    errors = exc_info.value.errors()
    assert errors[0]["loc"] == (field,)
    assert "must not be empty" in errors[0]["msg"]


def test_event_create_keeps_surrounding_whitespace_after_validation():
    payload = EventCreate(
        title=" Launch ",
        starts_at=START,
        ends_at=END,
    )

    assert payload.title == " Launch "


def test_event_update_supports_partial_payloads():
    payload = EventUpdate(title="Renamed")

    assert payload.title == "Renamed"
    assert payload.description is None
    assert payload.location is None
    assert payload.starts_at is None
    assert payload.ends_at is None
    assert payload.model_dump(exclude_unset=True) == {"title": "Renamed"}


@pytest.mark.parametrize("field", ["title", "description", "location"])
def test_event_update_rejects_blank_text(field):
    with pytest.raises(ValidationError):
        EventUpdate(**{field: "  "})


def test_event_read_from_model_serializes_all_fields():
    event = Event(
        id=7,
        title="Launch",
        description=None,
        location="Berlin",
        starts_at=START,
        ends_at=END,
        created_at=START,
        updated_at=END,
    )

    read = EventRead.from_model(event)

    assert read.id == 7
    assert read.title == "Launch"
    assert read.description is None
    assert read.location == "Berlin"
    assert read.starts_at == START
    assert read.ends_at == END
    assert read.created_at == START
    assert read.updated_at == END
