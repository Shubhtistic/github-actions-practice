from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from src.actions.api.validation import reject_blank_text
from src.actions.events.models import Event


# --- Create ---
class EventCreate(BaseModel):
    title: str
    description: str | None = None
    location: str | None = None
    starts_at: datetime
    ends_at: datetime

    _check_text = field_validator("title", "description", "location", mode="before")(
        reject_blank_text
    )


# --- Update (partial) ---
class EventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    location: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    _check_text = field_validator("title", "description", "location", mode="before")(
        reject_blank_text
    )


# --- Read ---
class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    location: str | None
    starts_at: datetime
    ends_at: datetime
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, event: Event) -> EventRead:
        return cls.model_validate(event)
