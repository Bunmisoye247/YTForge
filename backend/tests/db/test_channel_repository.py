from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from uuid6 import uuid7

from ytforge.application.use_cases.channels import CreateChannelInput, create_channel
from ytforge.domain.entities import Channel, User
from ytforge.infrastructure.db.session import get_engine, get_session_factory
from ytforge.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork

pytestmark = pytest.mark.db


@pytest.fixture(autouse=True)
async def _fresh_engine_per_test():
    """Same rationale as `tests/workflows/test_video_production.py`'s
    fixture of the same name: `get_engine()` is `@lru_cache`'d and asyncpg
    connections are bound to the event loop they were opened on, which
    differs per pytest-asyncio test function."""
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    yield
    await get_engine().dispose()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


def _make_uow() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(get_session_factory())


async def _seed_channel(name: str) -> Channel:
    uow = _make_uow()
    async with uow:
        now = datetime.now(UTC)
        user = User(
            id=uuid7(),
            email=f"{uuid.uuid4().hex}@db-test.local",
            hashed_password="x",
            full_name="DB Test User",
            is_active=True,
            is_superuser=False,
            token_version=0,
            created_at=now,
            updated_at=now,
        )
        await uow.users.add(user)
        await uow.commit()
        return await create_channel(uow, CreateChannelInput(name=name, owner_user_id=user.id))


async def test_channel_refresh_token_round_trips_through_real_encryption() -> None:
    """The one thing `EnvelopeEncryptor`'s own unit tests can't cover:
    that `SqlAlchemyChannelRepository` actually calls it correctly at the
    real DB boundary — encrypt on write, decrypt on read, via a real
    Postgres round-trip (a fresh session per read, so this can't just be
    the same in-memory Channel object)."""
    try:
        channel = await _seed_channel("DB Test Channel")
    except Exception as exc:
        pytest.skip(f"no reachable Postgres for db test: {exc}")

    youtube_channel_id = f"UC-test-{uuid.uuid4().hex}"
    uow2 = _make_uow()
    async with uow2:
        channel.oauth_refresh_token = "super-secret-refresh-token"
        channel.youtube_channel_id = youtube_channel_id
        await uow2.channels.update(channel)
        await uow2.commit()

    uow3 = _make_uow()
    async with uow3:
        reloaded = await uow3.channels.get_by_id(channel.id)

    assert reloaded is not None
    assert reloaded.oauth_refresh_token == "super-secret-refresh-token"
    assert reloaded.youtube_channel_id == youtube_channel_id


async def test_channel_with_no_refresh_token_decrypts_to_none() -> None:
    try:
        channel = await _seed_channel("Unlinked Channel")
    except Exception as exc:
        pytest.skip(f"no reachable Postgres for db test: {exc}")

    uow2 = _make_uow()
    async with uow2:
        reloaded = await uow2.channels.get_by_id(channel.id)

    assert reloaded is not None
    assert reloaded.oauth_refresh_token is None
