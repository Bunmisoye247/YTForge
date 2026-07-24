from __future__ import annotations

import uuid
from typing import Any, Protocol


class EventPublisher(Protocol):
    """Redis Streams sink for the outbox relay (ARCHITECTURE.md §2.3/§5.3):
    `infrastructure/events/relay.py` reads PENDING rows from the
    transactional outbox and calls `publish` for each — this port is never
    called directly from use cases, only from the relay, keeping the
    outbox → Redis hop transactional-write-then-async-publish (at-least-
    once, consumers must be idempotent)."""

    async def publish(
        self, *, event_id: uuid.UUID, event_type: str, aggregate_type: str, aggregate_id: uuid.UUID, payload: dict[str, Any]
    ) -> None: ...
