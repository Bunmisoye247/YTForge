from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any, cast

import redis.asyncio as redis

from ytforge.infrastructure.telemetry.pipeline_metrics import dlq_moves

logger = logging.getLogger("ytforge.events.consumer")

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]


def _decode_fields(fields: dict[Any, Any]) -> dict[str, Any]:
    decoded = {
        (k.decode() if isinstance(k, bytes) else k): (v.decode() if isinstance(v, bytes) else v)
        for k, v in fields.items()
    }
    if "payload" in decoded:
        decoded["payload"] = json.loads(decoded["payload"])
    return decoded


class StreamConsumer:
    """Consumes the main events stream via a durable consumer group
    (ARCHITECTURE.md §5.3). A handler that raises moves its message to
    `events:dlq` (with the original fields plus the error) and ACKs it off
    the main stream — single-attempt-then-DLQ, no in-process retry loop,
    matching this codebase's preference for simple, explicit failure paths
    over speculative retry machinery. `claim_stale_entries` recovers
    messages left pending by a crashed consumer instance ("Redis Streams
    pending-entry claiming" per the architecture doc)."""

    def __init__(
        self,
        client: redis.Redis,
        stream: str,
        dlq_stream: str,
        consumer_group: str,
        consumer_name: str,
        handlers: dict[str, EventHandler],
    ) -> None:
        self._client = client
        self._stream = stream
        self._dlq_stream = dlq_stream
        self._consumer_group = consumer_group
        self._consumer_name = consumer_name
        self._handlers = handlers
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

    async def poll_once(self, count: int = 10, block_ms: int = 1000) -> int:
        """One `XREADGROUP` pass. Returns the number of messages processed
        (handled or DLQ'd)."""
        await self._ensure_group()
        raw_response = await self._client.xreadgroup(
            self._consumer_group, self._consumer_name, {self._stream: ">"}, count=count, block=block_ms
        )
        if not raw_response:
            return 0
        response = cast("list[tuple[Any, list[tuple[Any, dict[Any, Any]]]]]", raw_response)

        processed = 0
        for _stream_name, messages in response:
            for message_id, raw_fields in messages:
                await self._handle_message(message_id, raw_fields)
                processed += 1
        return processed

    async def _handle_message(self, message_id: bytes | str, raw_fields: dict[Any, Any]) -> None:
        fields = _decode_fields(raw_fields)
        event_type = fields.get("event_type", "")
        handler = self._handlers.get(event_type)
        try:
            if handler is not None:
                await handler(fields)
        except Exception as exc:
            logger.exception("handler for %s failed on message %s, moving to DLQ", event_type, message_id)
            await self._move_to_dlq(raw_fields, str(exc))
        await self._client.xack(self._stream, self._consumer_group, message_id)

    async def _move_to_dlq(self, raw_fields: dict[Any, Any], error: str) -> None:
        dlq_fields = dict(raw_fields)
        dlq_fields["error"] = error
        await self._client.xadd(self._dlq_stream, dlq_fields)
        # ARCHITECTURE.md §9's "DLQ growth" alert — a moves-per-second rate
        # rather than absolute queue depth (nothing here polls XLEN
        # periodically); rate-of-growth is what the alert rule watches.
        dlq_moves.add(1, {"stream": self._stream})

    async def claim_stale_entries(self, min_idle_time: timedelta) -> int:
        """Reclaims pending entries idle longer than `min_idle_time`
        (assigned to a consumer that crashed before ACKing) onto this
        consumer, then processes them immediately. Returns the count
        claimed."""
        await self._ensure_group()
        _next_start, claimed, _deleted = await self._client.xautoclaim(
            self._stream, self._consumer_group, self._consumer_name, int(min_idle_time.total_seconds() * 1000)
        )
        for message_id, raw_fields in claimed:
            await self._handle_message(message_id, raw_fields)
        return len(claimed)
