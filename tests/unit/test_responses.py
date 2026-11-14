from datetime import UTC, datetime

import orjson

from src.actions.api.responses import ApiResponse


def _body(response: ApiResponse) -> dict:
    return orjson.loads(response.body)


def test_success_defaults():
    response = ApiResponse.success()

    assert response.status_code == 200
    assert response.media_type == "application/json"
    assert _body(response) == {
        "message": "Success",
        "status_code": 200,
        "data": None,
        "meta": None,
    }


def test_success_with_payload_and_metadata():
    response = ApiResponse.success(
        message="Events fetched",
        data=[{"id": 1}],
        code=201,
        meta={"count": 1},
    )

    assert response.status_code == 201
    assert _body(response) == {
        "message": "Events fetched",
        "status_code": 201,
        "data": [{"id": 1}],
        "meta": {"count": 1},
    }


def test_error_defaults():
    response = ApiResponse.error()

    assert response.status_code == 400
    assert _body(response) == {
        "message": "Something went wrong",
        "status_code": 400,
        "data": None,
        "meta": None,
    }


def test_error_with_custom_code_and_details():
    response = ApiResponse.error(
        message="Event 42 not found",
        code=404,
        meta={"path": "/events/42"},
    )

    assert response.status_code == 404
    body = _body(response)
    assert body["status_code"] == 404
    assert body["message"] == "Event 42 not found"
    assert body["meta"] == {"path": "/events/42"}


def test_render_serializes_datetimes_and_unknown_types():
    moment = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)

    rendered = ApiResponse.success(data={"at": moment}).body

    assert orjson.loads(rendered)["data"]["at"].startswith("2026-11-15T12:00:00")


def test_render_uses_str_for_non_serializable_values():
    class Thing:
        def __str__(self) -> str:
            return "thing"

    body = orjson.loads(ApiResponse.success(data={"thing": Thing()}).body)

    assert body["data"] == {"thing": "thing"}
