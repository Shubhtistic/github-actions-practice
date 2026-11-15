from typing import Any

from src.actions.infrastructure.config import (
    AppSettings,
    PostgresSettings,
    Settings,
    get_settings,
)


def _postgres_settings(**overrides: Any) -> PostgresSettings:
    values = {
        "POSTGRES_SERVER": "db.local",
        "POSTGRES_PORT": 5432,
        "POSTGRES_USER": "alice",
        "POSTGRES_PASSWORD": "secret",
        "POSTGRES_DB": "events",
    }
    values.update(overrides)
    return PostgresSettings.model_validate(values)


def test_postgres_settings_build_async_url():
    settings = _postgres_settings()

    assert settings.postgres_async_url == (
        "postgresql+asyncpg://alice:secret@db.local:5432/events"
    )


def test_postgres_settings_reflect_overrides():
    settings = _postgres_settings(
        POSTGRES_SERVER="replica",
        POSTGRES_PORT=6543,
        POSTGRES_DB="analytics",
    )

    assert settings.postgres_async_url == (
        "postgresql+asyncpg://alice:secret@replica:6543/analytics"
    )


def test_app_settings_reads_aliases():
    settings = AppSettings(
        _env_file=None,
        ENVIRONMENT="test",
        PROJECT_NAME="actions",
        VERSION="9.9.9",
    )

    assert settings.environment == "test"
    assert settings.project_name == "actions"
    assert settings.version == "9.9.9"


def test_settings_combines_app_and_postgres(monkeypatch):
    for key, value in {
        "ENVIRONMENT": "test",
        "PROJECT_NAME": "actions",
        "VERSION": "1.2.3",
        "POSTGRES_SERVER": "localhost",
        "POSTGRES_PORT": "5433",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "postgres",
        "POSTGRES_DB": "actions",
    }.items():
        monkeypatch.setenv(key, value)

    get_settings.cache_clear()
    try:
        settings = get_settings()
    finally:
        get_settings.cache_clear()

    assert isinstance(settings, Settings)
    assert settings.app.project_name == "actions"
    assert settings.postgres.postgres_async_url == (
        "postgresql+asyncpg://postgres:postgres@localhost:5433/actions"
    )


def test_get_settings_is_cached(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("PROJECT_NAME", "actions")
    monkeypatch.setenv("VERSION", "1.0.0")
    monkeypatch.setenv("POSTGRES_SERVER", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_USER", "postgres")
    monkeypatch.setenv("POSTGRES_PASSWORD", "postgres")
    monkeypatch.setenv("POSTGRES_DB", "actions")

    get_settings.cache_clear()
    try:
        assert get_settings() is get_settings()
    finally:
        get_settings.cache_clear()
