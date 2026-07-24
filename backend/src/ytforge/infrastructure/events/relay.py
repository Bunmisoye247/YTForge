from __future__ import annotations

import logging

from ytforge.application.ports.providers import EventPublisher, UnitOfWork

logger = logging.getLogger("ytforge.events.relay")


async def relay_outbox_once(uow: UnitOfWork, publisher: EventPublisher, batch_size: int = 100) -> int:
    """One pass of the transactional-outbox relay (ARCHITECTURE.md §2.3):
    read PENDING rows, publish each to Redis Streams, mark PUBLISHED. A
    publish failure marks the row FAILED rather than raising, so one bad
    event never wedges the relay loop — operators inspect FAILED rows the
    same way DLQ entries are inspected on the consumer side. Returns the
    number of rows processed (published + failed) for the caller to log/
    decide whether to keep polling."""
    pending = await uow.outbox.list_pending(limit=batch_size)
    processed = 0
    for event in pending:
        try:
            await publisher.publish(
                event_id=event.id,
                event_type=event.event_type,
                aggregate_type=event.aggregate_type,
                aggregate_id=event.aggregate_id,
                payload=event.payload,
            )
        except Exception:
            logger.exception("failed to relay outbox event %s (%s)", event.id, event.event_type)
            await uow.outbox.mark_failed(event.id)
        else:
            await uow.outbox.mark_published(event.id)
        processed += 1
    await uow.commit()
    return processed
