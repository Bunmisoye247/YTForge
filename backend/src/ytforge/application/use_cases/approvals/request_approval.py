from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from uuid6 import uuid7

from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Approval
from ytforge.domain.enums import ApprovalKind, ApprovalStatus


@dataclass(frozen=True, slots=True)
class RequestApprovalInput:
    kind: ApprovalKind
    requested_by_user_id: uuid.UUID
    payload: dict[str, Any] = field(default_factory=dict)
    workflow_id: str | None = None


async def request_approval(uow: UnitOfWork, data: RequestApprovalInput) -> Approval:
    now = datetime.now(UTC)
    approval = Approval(
        id=uuid7(),
        kind=data.kind,
        status=ApprovalStatus.PENDING,
        payload=data.payload,
        workflow_id=data.workflow_id,
        requested_by_user_id=data.requested_by_user_id,
        created_at=now,
        updated_at=now,
    )
    await uow.approvals.add(approval)
    await uow.commit()
    return approval
