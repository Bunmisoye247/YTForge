from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from uuid6 import uuid7

from ytforge.application.common.errors import InvalidStateError, NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.use_cases.assets.orphan_asset import orphan_asset
from ytforge.domain.entities import Approval, AuditLog
from ytforge.domain.enums import ApprovalKind, ApprovalStatus
from ytforge.domain.errors import InvalidTransitionError


@dataclass(frozen=True, slots=True)
class DecideApprovalInput:
    status: ApprovalStatus
    decided_by_user_id: uuid.UUID
    note: str | None = None


async def decide_approval(
    uow: UnitOfWork, approval_id: uuid.UUID, data: DecideApprovalInput
) -> Approval:
    approval = await uow.approvals.get_by_id(approval_id)
    if approval is None:
        raise NotFoundError("Approval", approval_id)

    before_status = approval.status
    now = datetime.now(UTC)
    try:
        approval.decide(
            status=data.status,
            decided_by_user_id=data.decided_by_user_id,
            decided_at=now,
            note=data.note,
        )
    except InvalidTransitionError as exc:
        raise InvalidStateError(exc) from exc

    await uow.approvals.update(approval)
    await uow.audit_logs.add(
        AuditLog(
            id=uuid7(),
            actor_user_id=data.decided_by_user_id,
            action="approval.decided",
            entity_type="approval",
            entity_id=approval.id,
            before={"status": before_status.value},
            after={"status": approval.status.value},
        )
    )
    await uow.add_event(
        aggregate_type="approval",
        aggregate_id=approval.id,
        event_type="ApprovalGranted" if data.status == ApprovalStatus.APPROVED else "ApprovalRejected",
        payload={"decided_by_user_id": str(data.decided_by_user_id)},
    )
    await uow.commit()

    if approval.status == ApprovalStatus.APPROVED and approval.kind == ApprovalKind.ASSET_DELETION:
        asset_id = uuid.UUID(approval.payload["asset_id"])
        await orphan_asset(uow, asset_id)

    return approval
