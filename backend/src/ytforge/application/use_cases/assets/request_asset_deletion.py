from __future__ import annotations

import uuid
from datetime import UTC, datetime

from uuid6 import uuid7

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Approval
from ytforge.domain.enums import ApprovalKind, ApprovalStatus


async def request_asset_deletion(
    uow: UnitOfWork, asset_id: uuid.UUID, requested_by_user_id: uuid.UUID
) -> Approval:
    if await uow.assets.get_by_id(asset_id) is None:
        raise NotFoundError("Asset", asset_id)

    now = datetime.now(UTC)
    approval = Approval(
        id=uuid7(),
        kind=ApprovalKind.ASSET_DELETION,
        status=ApprovalStatus.PENDING,
        payload={"asset_id": str(asset_id)},
        requested_by_user_id=requested_by_user_id,
        created_at=now,
        updated_at=now,
    )
    await uow.approvals.add(approval)
    await uow.commit()
    return approval
