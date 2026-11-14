from src.actions.events import repo
from src.actions.events.exceptions import (
    EventNotFoundError,
    InvalidEventTimeError,
)
from src.actions.events.models import Event
from src.actions.events.schemas import EventCreate, EventUpdate
from src.actions.infrastructure.database import get_db_session


class EventService:
    @staticmethod
    async def create_event(payload: EventCreate) -> Event:
        EventService._validate_times(payload.starts_at, payload.ends_at)
        event = Event(**payload.model_dump())
        async with get_db_session() as db_session:
            return await repo.create_event(event, db_session)

    @staticmethod
    async def get_event(event_id: int) -> Event:
        async with get_db_session() as db_session:
            event = await repo.get_event(event_id, db_session)
            if event is None:
                raise EventNotFoundError(event_id)
            return event

    @staticmethod
    async def list_events(
        limit: int = 20,
        offset: int = 0,
    ) -> list[Event]:
        async with get_db_session() as db_session:
            return await repo.list_events(db_session, limit=limit, offset=offset)

    @staticmethod
    async def update_event(
        event_id: int,
        payload: EventUpdate,
    ) -> Event:
        async with get_db_session() as db_session:
            event = await repo.get_event(event_id, db_session)
            if event is None:
                raise EventNotFoundError(event_id)

            changes = payload.model_dump(exclude_unset=True)
            EventService._validate_times(
                changes.get("starts_at", event.starts_at),
                changes.get("ends_at", event.ends_at),
            )
            return await repo.update_event(event, changes, db_session)

    @staticmethod
    async def delete_event(event_id: int) -> None:
        async with get_db_session() as db_session:
            deleted = await repo.delete_event(event_id, db_session)
            if not deleted:
                raise EventNotFoundError(event_id)

    @staticmethod
    def _validate_times(starts_at, ends_at) -> None:
        if ends_at <= starts_at:
            raise InvalidEventTimeError
