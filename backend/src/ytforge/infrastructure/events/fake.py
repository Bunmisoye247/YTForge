from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class FakePublishedEvent:
    event_id: uuid.UUID
    event_type: str
    aggregate_type: str
    aggregate_id: uuid.UUID
    payload: dict[str, Any]


class FakeEventPublisher:
    """In-memory stand-in for `RedisStreamsEventPublisher` — no Redis
    server needed for tests."""

    def __init__(self) -> None:
        self.published: list[FakePublishedEvent] = []

    async def publish(
        self, *, event_id: uuid.UUID, event_type: str, aggregate_type: str, aggregate_id: uuid.UUID, payload: dict[str, Any]
    ) -> None:
        self.published.append(
            FakePublishedEvent(
                event_id=event_id,
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                payload=payload,
            )
        )
