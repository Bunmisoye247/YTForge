from __future__ import annotations

import logging
import uuid
from typing import Any

from uuid6 import uuid7

from ytforge.domain.entities import AuditLog
from ytforge.infrastructure.db.session import get_session_factory
from ytforge.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork

logger = logging.getLogger("ytforge.consumers")

_AUDITABLE_EVENT_TYPES = {"ApprovalGranted", "ApprovalRejected", "AssetOrphaned", "PipelineFailed"}


async def audit_handler(payload: dict[str, Any]) -> None:
    """Writes an `AuditLog` row for interesting event types — a second,
    independent record of "this happened" alongside whatever the
    triggering use case already wrote directly (defense in depth: this
    handler runs from the Redis Streams side, not the same transaction)."""
    event_type = payload.get("event_type", "")
    if event_type not in _AUDITABLE_EVENT_TYPES:
        return

    uow = SqlAlchemyUnitOfWork(get_session_factory())
    async with uow:
        await uow.audit_logs.add(
            AuditLog(
                id=uuid7(),
                actor_user_id=None,
                action=f"event.{event_type}",
                entity_type=payload.get("aggregate_type", "unknown"),
                entity_id=uuid.UUID(payload["aggregate_id"]) if payload.get("aggregate_id") else uuid7(),
                after=payload.get("payload"),
            )
        )
        await uow.commit()


async def notify_handler(payload: dict[str, Any]) -> None:
    """Stands in for "dashboard SSE + email/Slack notification"
    (ARCHITECTURE.md §5.2). No email/Slack integration exists — no
    credentials, no phase has assigned it — so this just logs at INFO
    level. The SSE half is handled separately by a live stream reader, not
    this durable consumer-group handler."""
    logger.info("notify: %s", payload)
