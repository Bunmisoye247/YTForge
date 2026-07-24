from __future__ import annotations

from typing import Any

import redis.asyncio as redis

from ytforge.infrastructure.events.consumer import StreamConsumer


class _FakeRedis:
    """Minimal in-memory stand-in for `redis.asyncio.Redis`'s stream
    commands — no real Redis server needed. Mirrors just enough of
    XGROUP CREATE/XREADGROUP/XACK/XADD/XAUTOCLAIM to exercise
    `StreamConsumer`'s consume-ack and DLQ-move logic."""

    def __init__(self) -> None:
        self.streams: dict[str, list[tuple[str, dict[str, Any]]]] = {}
        self.groups: dict[tuple[str, str], set[str]] = {}
        self.pending: dict[tuple[str, str], set[str]] = {}
        self._next_id = 1

    async def xgroup_create(self, name: str, groupname: str, id: str = "0", mkstream: bool = False) -> bool:
        if (name, groupname) in self.groups:
            raise redis.ResponseError("BUSYGROUP Consumer Group name already exists")
        self.streams.setdefault(name, [])
        self.groups[(name, groupname)] = set()
        self.pending[(name, groupname)] = set()
        return True

    async def xadd(self, name: str, fields: dict[str, Any], **kwargs: Any) -> str:
        message_id = f"{self._next_id}-0"
        self._next_id += 1
        self.streams.setdefault(name, []).append((message_id, dict(fields)))
        return message_id

    async def xreadgroup(
        self, groupname: str, consumername: str, streams: dict[str, str], count: int | None = None, block: int | None = None
    ) -> list[Any]:
        result = []
        for name in streams:
            delivered = self.groups.setdefault((name, groupname), set())
            undelivered = [(mid, f) for mid, f in self.streams.get(name, []) if mid not in delivered]
            batch = undelivered[:count] if count else undelivered
            for mid, _ in batch:
                delivered.add(mid)
                self.pending[(name, groupname)].add(mid)
            if batch:
                result.append((name, batch))
        return result

    async def xack(self, name: str, groupname: str, *ids: str) -> int:
        pending = self.pending.get((name, groupname), set())
        acked = 0
        for message_id in ids:
            if message_id in pending:
                pending.discard(message_id)
                acked += 1
        return acked

    async def xautoclaim(
        self, name: str, groupname: str, consumername: str, min_idle_time: int, start_id: str = "0-0", count: int | None = None
    ) -> list[Any]:
        pending_ids = self.pending.get((name, groupname), set())
        claimed = [(mid, f) for mid, f in self.streams.get(name, []) if mid in pending_ids]
        return ["0-0", claimed, []]


async def test_consumer_processes_message_and_acks_it() -> None:
    redis_client = _FakeRedis()
    handled: list[dict[str, Any]] = []

    async def handler(payload: dict[str, Any]) -> None:
        handled.append(payload)

    consumer = StreamConsumer(
        redis_client,  # type: ignore[arg-type]
        stream="events",
        dlq_stream="events:dlq",
        consumer_group="ytforge-consumers",
        consumer_name="worker-1",
        handlers={"ApprovalGranted": handler},
    )
    await redis_client.xadd(
        "events",
        {"event_id": "e1", "event_type": "ApprovalGranted", "aggregate_type": "approval", "aggregate_id": "a1", "payload": '{"foo": "bar"}'},
    )

    processed = await consumer.poll_once()

    assert processed == 1
    assert handled == [
        {"event_id": "e1", "event_type": "ApprovalGranted", "aggregate_type": "approval", "aggregate_id": "a1", "payload": {"foo": "bar"}}
    ]
    assert redis_client.pending[("events", "ytforge-consumers")] == set()


async def test_consumer_moves_failed_message_to_dlq_and_still_acks_main_stream() -> None:
    redis_client = _FakeRedis()

    async def failing_handler(payload: dict[str, Any]) -> None:
        raise RuntimeError("boom")

    consumer = StreamConsumer(
        redis_client,  # type: ignore[arg-type]
        stream="events",
        dlq_stream="events:dlq",
        consumer_group="ytforge-consumers",
        consumer_name="worker-1",
        handlers={"PipelineFailed": failing_handler},
    )
    await redis_client.xadd(
        "events",
        {"event_id": "e2", "event_type": "PipelineFailed", "aggregate_type": "project", "aggregate_id": "p1", "payload": "{}"},
    )

    processed = await consumer.poll_once()

    assert processed == 1
    assert redis_client.pending[("events", "ytforge-consumers")] == set()
    dlq_entries = redis_client.streams["events:dlq"]
    assert len(dlq_entries) == 1
    _mid, dlq_fields = dlq_entries[0]
    assert dlq_fields["event_type"] == "PipelineFailed"
    assert "boom" in dlq_fields["error"]


async def test_consumer_ignores_event_types_with_no_registered_handler() -> None:
    redis_client = _FakeRedis()
    consumer = StreamConsumer(
        redis_client,  # type: ignore[arg-type]
        stream="events",
        dlq_stream="events:dlq",
        consumer_group="ytforge-consumers",
        consumer_name="worker-1",
        handlers={},
    )
    await redis_client.xadd("events", {"event_id": "e3", "event_type": "SomeUnhandledEvent", "payload": "{}"})

    processed = await consumer.poll_once()

    assert processed == 1
    assert redis_client.streams.get("events:dlq", []) == []


async def test_claim_stale_entries_reprocesses_pending_messages() -> None:
    redis_client = _FakeRedis()
    handled: list[str] = []

    async def handler(payload: dict[str, Any]) -> None:
        handled.append(payload["event_id"])

    consumer = StreamConsumer(
        redis_client,  # type: ignore[arg-type]
        stream="events",
        dlq_stream="events:dlq",
        consumer_group="ytforge-consumers",
        consumer_name="worker-2",
        handlers={"ApprovalGranted": handler},
    )
    await redis_client.xgroup_create("events", "ytforge-consumers")
    # Simulate a message delivered to a now-crashed consumer that never ACKed.
    redis_client.streams["events"].append(
        ("99-0", {"event_id": "stale-1", "event_type": "ApprovalGranted", "payload": "{}"})
    )
    redis_client.groups[("events", "ytforge-consumers")].add("99-0")
    redis_client.pending[("events", "ytforge-consumers")].add("99-0")

    from datetime import timedelta

    claimed_count = await consumer.claim_stale_entries(timedelta(minutes=5))

    assert claimed_count == 1
    assert handled == ["stale-1"]
