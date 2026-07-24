from __future__ import annotations

import asyncio
import logging

import redis.asyncio as redis

from ytforge.infrastructure.config.settings import Settings, get_settings
from ytforge.infrastructure.db.session import get_session_factory
from ytforge.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from ytforge.infrastructure.events.fake import FakeEventPublisher
from ytforge.infrastructure.events.redis_streams import RedisStreamsEventPublisher
from ytforge.infrastructure.events.relay import relay_outbox_once
from ytforge.infrastructure.telemetry.otel_setup import configure_otel

logger = logging.getLogger("ytforge.relay")

_RELAY_INTERVAL_SECONDS = 3.0


async def run_relay() -> None:
    """The `outbox-relay` deployable unit (ARCHITECTURE.md §13's `core`
    compose profile lists it separately from `worker`) — polls the
    transactional outbox and republishes to Redis Streams. Its own
    container so a slow/backed-up relay never competes with workflow/
    activity task processing on the main worker."""
    settings = get_settings()
    configure_otel(settings.observability)
    publisher = _build_publisher(settings)

    logger.info("starting ytforge outbox relay")
    while True:
        uow = SqlAlchemyUnitOfWork(get_session_factory())
        async with uow:
            try:
                processed = await relay_outbox_once(uow, publisher)
                if processed:
                    logger.info("relayed %d outbox event(s)", processed)
            except Exception:
                logger.exception("outbox relay pass failed")
        await asyncio.sleep(_RELAY_INTERVAL_SECONDS)


def _build_publisher(settings: Settings) -> FakeEventPublisher | RedisStreamsEventPublisher:
    if settings.models.provider_set == "fake":
        return FakeEventPublisher()
    return RedisStreamsEventPublisher(
        redis.from_url(settings.redis.url), settings.redis.events_stream, settings.redis.consumer_group
    )
