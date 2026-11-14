import pytest

from src.actions.events.exceptions import (
    EventNotFoundError,
    EventServiceError,
    InvalidEventTimeError,
)


def test_base_error_default_status_code():
    error = EventServiceError("boom")

    assert error.status_code == 400
    assert str(error) == "boom"


def test_not_found_error_message_and_metadata():
    error = EventNotFoundError(42)

    assert error.status_code == 404
    assert error.event_id == 42
    assert str(error) == "Event 42 not found"
    assert isinstance(error, EventServiceError)


def test_invalid_time_error_message_and_status_code():
    error = InvalidEventTimeError()

    assert error.status_code == 422
    assert str(error) == "ends_at must be after starts_at"
    assert isinstance(error, EventServiceError)


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (EventNotFoundError(1), 404),
        (InvalidEventTimeError(), 422),
    ],
)
def test_subclasses_are_catchable_as_service_errors(error, status_code):
    with pytest.raises(EventServiceError) as exc_info:
        raise error

    assert exc_info.value.status_code == status_code
