from fastapi import APIRouter, Query

from src.actions.api.responses import ApiResponse
from src.actions.events.exceptions import (
    EventNotFoundError,
    InvalidEventTimeError,
)
from src.actions.events.schemas import EventCreate, EventRead, EventUpdate
from src.actions.events.service import EventService

router = APIRouter(prefix="/events", tags=["events"])


@router.post("")
async def create_event(payload: EventCreate):
    try:
        event = await EventService.create_event(payload)
    except InvalidEventTimeError as exc:
        return ApiResponse.error(message=str(exc), code=422)
    return ApiResponse.success(
        message="Event created",
        data=EventRead.from_model(event).model_dump(mode="json"),
        code=201,
    )


@router.get("/{event_id}")
async def get_event(event_id: int):
    try:
        event = await EventService.get_event(event_id)
    except EventNotFoundError as exc:
        return ApiResponse.error(message=str(exc), code=404)
    return ApiResponse.success(
        message="Event fetched",
        data=EventRead.from_model(event).model_dump(mode="json"),
    )


@router.get("")
async def list_events(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    events = await EventService.list_events(limit=limit, offset=offset)
    return ApiResponse.success(
        message="Events fetched",
        data=[EventRead.from_model(e).model_dump(mode="json") for e in events],
        meta={"limit": limit, "offset": offset, "count": len(events)},
    )


@router.patch("/{event_id}")
async def update_event(event_id: int, payload: EventUpdate):
    try:
        event = await EventService.update_event(event_id, payload)
    except EventNotFoundError as exc:
        return ApiResponse.error(message=str(exc), code=404)
    except InvalidEventTimeError as exc:
        return ApiResponse.error(message=str(exc), code=422)
    return ApiResponse.success(
        message="Event updated",
        data=EventRead.from_model(event).model_dump(mode="json"),
    )


@router.delete("/{event_id}")
async def delete_event(event_id: int):
    try:
        await EventService.delete_event(event_id)
    except EventNotFoundError as exc:
        return ApiResponse.error(message=str(exc), code=404)
    return ApiResponse.success(message=f"Event {event_id} deleted")
