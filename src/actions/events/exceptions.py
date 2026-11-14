class EventServiceError(Exception):
    status_code = 400


class EventNotFoundError(EventServiceError):
    status_code = 404

    def __init__(self, event_id: int) -> None:
        super().__init__(f"Event {event_id} not found")
        self.event_id = event_id


class InvalidEventTimeError(EventServiceError):
    status_code = 422

    def __init__(self) -> None:
        super().__init__("ends_at must be after starts_at")
