from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.actions.main import app

START = datetime(2026, 11, 15, 10, 0, tzinfo=UTC)
END = START + timedelta(hours=2)

pytestmark = pytest.mark.usefixtures("use_test_db")


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


def _payload(**overrides) -> dict:
    values = {
        "title": "Launch",
        "description": "Ship it",
        "location": "Remote",
        "starts_at": START.isoformat(),
        "ends_at": END.isoformat(),
    }
    values.update(overrides)
    return values


async def _create(client: AsyncClient, **overrides) -> dict:
    response = await client.post("/events", json=_payload(**overrides))
    assert response.status_code == 201
    return response.json()["data"]


async def test_create_event_returns_created_payload(client):
    response = await client.post("/events", json=_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Event created"
    assert body["status_code"] == 201
    assert body["meta"] is None
    assert body["data"]["id"] > 0
    assert body["data"]["title"] == "Launch"
    assert body["data"]["description"] == "Ship it"
    assert body["data"]["location"] == "Remote"

    starts_at = datetime.fromisoformat(body["data"]["starts_at"])
    assert starts_at == START
    assert starts_at.tzinfo is not None


async def test_create_event_rejects_blank_title(client):
    response = await client.post("/events", json=_payload(title="   "))

    assert response.status_code == 422
    body = response.json()
    assert body["message"] == "Validation failed"
    assert body["status_code"] == 422
    assert body["meta"]["path"].endswith("/events")
    assert body["meta"]["errors"][0]["loc"] == ["body", "title"]


async def test_create_event_rejects_invalid_time_range(client):
    response = await client.post(
        "/events", json=_payload(starts_at=END.isoformat(), ends_at=START.isoformat())
    )

    assert response.status_code == 422
    body = response.json()
    assert body["message"] == "ends_at must be after starts_at"
    assert body["status_code"] == 422


async def test_get_event_returns_existing_event(client):
    created = await _create(client)

    response = await client.get(f"/events/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Event fetched"
    assert body["data"]["id"] == created["id"]


async def test_get_event_returns_404_when_missing(client):
    response = await client.get("/events/999999")

    assert response.status_code == 404
    body = response.json()
    assert body["message"] == "Event 999999 not found"
    assert body["status_code"] == 404


async def test_list_events_returns_paginated_metadata(client):
    for index in range(3):
        await _create(
            client,
            title=f"Event {index}",
            starts_at=(START + timedelta(days=index)).isoformat(),
            ends_at=(START + timedelta(days=index, hours=1)).isoformat(),
        )

    response = await client.get("/events", params={"limit": 2, "offset": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Events fetched"
    assert [event["title"] for event in body["data"]] == ["Event 1", "Event 2"]
    assert body["meta"] == {"limit": 2, "offset": 1, "count": 2}


async def test_list_events_rejects_invalid_limit(client):
    response = await client.get("/events", params={"limit": 0})

    assert response.status_code == 422
    assert response.json()["message"] == "Validation failed"


async def test_list_events_rejects_negative_offset(client):
    response = await client.get("/events", params={"offset": -1})

    assert response.status_code == 422


async def test_update_event_patches_only_provided_fields(client):
    created = await _create(client)

    response = await client.patch(f"/events/{created['id']}", json={"title": "Renamed"})

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Event updated"
    assert body["data"]["title"] == "Renamed"
    assert body["data"]["description"] == "Ship it"
    assert body["data"]["location"] == "Remote"

    fetched = await client.get(f"/events/{created['id']}")
    assert fetched.json()["data"]["title"] == "Renamed"


async def test_update_event_rejects_invalid_merged_time_range(client):
    created = await _create(client)

    response = await client.patch(
        f"/events/{created['id']}",
        json={"ends_at": (START - timedelta(minutes=1)).isoformat()},
    )

    assert response.status_code == 422
    assert response.json()["message"] == "ends_at must be after starts_at"


async def test_update_event_returns_404_when_missing(client):
    response = await client.patch("/events/999999", json={"title": "Renamed"})

    assert response.status_code == 404
    assert response.json()["message"] == "Event 999999 not found"


async def test_update_event_rejects_blank_title(client):
    created = await _create(client)

    response = await client.patch(f"/events/{created['id']}", json={"title": "  "})

    assert response.status_code == 422
    assert response.json()["message"] == "Validation failed"


async def test_delete_event_removes_row(client):
    created = await _create(client)

    response = await client.delete(f"/events/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == f"Event {created['id']} deleted"

    follow_up = await client.get(f"/events/{created['id']}")
    assert follow_up.status_code == 404


async def test_delete_event_returns_404_when_missing(client):
    response = await client.delete("/events/999999")

    assert response.status_code == 404
    assert response.json()["message"] == "Event 999999 not found"


async def test_scalar_docs_are_served(client):
    response = await client.get("/scalar")

    assert response.status_code == 200
    assert "html" in response.text.lower()
