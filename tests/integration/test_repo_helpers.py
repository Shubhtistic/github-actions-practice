from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from src.actions.events.models import Event
from src.actions.infrastructure.repo_helpers import (
    check_exists,
    create,
    delete_by_id,
    execute_query,
    get_all,
    get_one,
    get_one_by_query,
)
from tests.conftest import make_event

START = datetime(2026, 11, 15, 10, 0, tzinfo=UTC)


async def test_create_flushes_and_assigns_primary_key(db_session):
    created = await create(make_event(title="Created"), db_session)

    assert created.id is not None
    assert created.title == "Created"


async def test_get_one_returns_row_by_primary_key(db_session):
    created = await create(make_event(), db_session)

    fetched = await get_one(Event, created.id, db_session)
    missing = await get_one(Event, 999_999, db_session)

    assert fetched is not None
    assert fetched.id == created.id
    assert missing is None


async def test_get_all_applies_statement(db_session):
    await create(
        make_event(title="Later", starts_at=START + timedelta(days=2)), db_session
    )
    await create(make_event(title="Earlier", starts_at=START), db_session)

    rows = await get_all(select(Event).order_by(Event.starts_at), db_session)

    assert [row.title for row in rows] == ["Earlier", "Later"]


async def test_delete_by_id_reports_whether_row_was_deleted(db_session):
    created = await create(make_event(), db_session)

    assert await delete_by_id(Event, created.id, db_session) is True
    assert await delete_by_id(Event, created.id, db_session) is False
    assert await get_one(Event, created.id, db_session) is None


async def test_check_exists_without_and_with_filters(db_session):
    await create(make_event(title="Unique"), db_session)

    assert await check_exists(Event, db_session) is True
    assert await check_exists(Event, db_session, {"title": "Unique"}) is True
    assert await check_exists(Event, db_session, {"title": "Other"}) is False


async def test_check_exists_on_empty_table(db_session):
    assert await check_exists(Event, db_session) is False


async def test_get_one_by_query(db_session):
    created = await create(make_event(title="Find me"), db_session)

    found = await get_one_by_query(
        select(Event).where(Event.id == created.id), db_session
    )
    missing = await get_one_by_query(
        select(Event).where(Event.id == 999_999), db_session
    )

    assert found is not None
    assert found.title == "Find me"
    assert missing is None


async def test_execute_query_returns_raw_result(db_session):
    await create(make_event(title="A"), db_session)
    await create(make_event(title="B"), db_session)

    result = await execute_query(select(Event.title).order_by(Event.title), db_session)

    assert result.scalars().all() == ["A", "B"]


@pytest.mark.parametrize("limit", [1, 5])
async def test_get_all_respects_limit(db_session, limit):
    for index in range(5):
        await create(make_event(title=f"Event {index}"), db_session)

    rows = await get_all(select(Event).limit(limit), db_session)

    assert len(rows) == limit
