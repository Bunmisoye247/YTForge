from __future__ import annotations

import json
import uuid
from typing import Any

import redis.asyncio as redis

from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call


class RedisStreamsEventPublisher:
    """Publishes outbox events onto a single Redis Stream (ARCHITECTURE.md
    §2.3/§5.3) — one stream for all event types, consumers filter by
    `event_type` field. A consumer group is ensured on first publish so
    `XREADGROUP` works immediately without a separate provisioning step."""

    def __init__(self, client: redis.Redis, stream: str, consumer_group: str) -> None:
        self._client = client
        self._stream = stream
        self._consumer_group = consumer_group
        self._group_ready = False

    async def _ensure_group(self) -> None:
        if self._group_ready:
            return
        try:
            await self._client.xgroup_create(self._stream, self._consumer_group, id="0", mkstream=True)
        except redis.ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise
        self._group_ready = True

    async def publish(
        self, *, event_id: uuid.UUID, event_type: str, aggregate_type: str, aggregate_id: uuid.UUID, payload: dict[str, Any]
    ) -> None:
        async with record_provider_call("redis_streams", "events.publish"):
            await self._ensure_group()
            await self._client.xadd(
                self._stream,
                {
                    "event_id": str(event_id),
                    "event_type": event_type,
                    "aggregate_type": aggregate_type,
                    "aggregate_id": str(aggregate_id),
                    "payload": json.dumps(payload),
                },
            )
