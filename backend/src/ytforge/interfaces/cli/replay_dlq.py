from __future__ import annotations

from typing import Any, cast

import redis.asyncio as redis

from ytforge.infrastructure.config.settings import get_settings


def _decode(fields: dict[Any, Any]) -> dict[str, str]:
    return {
        (k.decode() if isinstance(k, bytes) else k): (v.decode() if isinstance(v, bytes) else v)
        for k, v in fields.items()
    }


async def list_dlq() -> None:
    """CLI stand-in for the "operator UI for inspect/replay/discard"
    ARCHITECTURE.md §5.3 calls for — same role `run-agent` plays for
    invoking agents manually until a real dashboard surface exists."""
    settings = get_settings()
    client = redis.from_url(settings.redis.url)
    entries = await client.xrange(settings.redis.events_dlq_stream, "-", "+")
    if not entries:
        print("DLQ is empty.")
        return
    for message_id, raw_fields in entries:
        fields = _decode(raw_fields or {})
        mid = message_id.decode() if isinstance(message_id, bytes) else message_id
        print(f"{mid}  event_type={fields.get('event_type')!r}  error={fields.get('error')!r}")


async def replay_dlq_entry(message_id: str) -> None:
    settings = get_settings()
    client = redis.from_url(settings.redis.url)
    entries = await client.xrange(settings.redis.events_dlq_stream, message_id, message_id)
    if not entries:
        print(f"No DLQ entry with id {message_id!r}.")
        return
    _found_id, raw_fields = entries[0]
    fields = _decode(raw_fields or {})
    fields.pop("error", None)
    await client.xadd(settings.redis.events_stream, cast("dict[Any, Any]", fields))
    await client.xdel(settings.redis.events_dlq_stream, message_id)
    print(f"Replayed {message_id} back onto {settings.redis.events_stream!r}.")


async def discard_dlq_entry(message_id: str) -> None:
    settings = get_settings()
    client = redis.from_url(settings.redis.url)
    removed = await client.xdel(settings.redis.events_dlq_stream, message_id)
    if removed:
        print(f"Discarded {message_id}.")
    else:
        print(f"No DLQ entry with id {message_id!r}.")
