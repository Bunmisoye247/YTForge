from __future__ import annotations

from uuid6 import uuid7

from fixtures.fakes import FakeUnitOfWork
from ytforge.application.ports.providers import EventPublisher
from ytforge.domain.enums import OutboxStatus
from ytforge.infrastructure.events.fake import FakeEventPublisher
from ytforge.infrastructure.events.relay import relay_outbox_once


async def test_relay_publishes_pending_events_and_marks_them_published() -> None:
    uow = FakeUnitOfWork()
    await uow.add_event(
        aggregate_type="project", aggregate_id=uuid7(), event_type="ProjectCreated", payload={"foo": "bar"}
    )
    publisher = FakeEventPublisher()

    processed = await relay_outbox_once(uow, publisher)

    assert processed == 1
    assert len(publisher.published) == 1
    assert publisher.published[0].event_type == "ProjectCreated"
    assert publisher.published[0].payload == {"foo": "bar"}
    stored = next(iter(uow.outbox.items.values()))
    assert stored.status == OutboxStatus.PUBLISHED
    assert stored.published_at is not None


async def test_relay_ignores_already_published_events() -> None:
    uow = FakeUnitOfWork()
    await uow.add_event(aggregate_type="project", aggregate_id=uuid7(), event_type="ProjectCreated", payload={})
    publisher = FakeEventPublisher()
    await relay_outbox_once(uow, publisher)

    processed_again = await relay_outbox_once(uow, publisher)

    assert processed_again == 0
    assert len(publisher.published) == 1


async def test_relay_marks_event_failed_when_publish_raises() -> None:
    class _FailingPublisher:
        async def publish(self, **kwargs: object) -> None:
            raise RuntimeError("redis unreachable")

    uow = FakeUnitOfWork()
    await uow.add_event(aggregate_type="project", aggregate_id=uuid7(), event_type="ProjectCreated", payload={})

    publisher: EventPublisher = _FailingPublisher()  # type: ignore[assignment]
    processed = await relay_outbox_once(uow, publisher)

    assert processed == 1
    stored = next(iter(uow.outbox.items.values()))
    assert stored.status == OutboxStatus.FAILED


async def test_relay_respects_batch_size() -> None:
    uow = FakeUnitOfWork()
    for _ in range(5):
        await uow.add_event(aggregate_type="project", aggregate_id=uuid7(), event_type="ProjectCreated", payload={})
    publisher = FakeEventPublisher()

    processed = await relay_outbox_once(uow, publisher, batch_size=2)

    assert processed == 2
    assert len(publisher.published) == 2
