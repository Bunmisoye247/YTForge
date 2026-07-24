from __future__ import annotations

import uuid
from datetime import UTC, datetime

from uuid6 import uuid7

from ytforge.application.common.errors import ConflictError, NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Approval
from ytforge.domain.enums import ApprovalKind, ApprovalStatus, VideoStatus


async def request_publish_approval(
    uow: UnitOfWork, video_id: uuid.UUID, requested_by_user_id: uuid.UUID
) -> Approval:
    """Creates the publish approval row. The actual YouTube upload — which
    transitions the video out of DRAFT and debits the quota ledger — is
    Phase-8 code triggered once this approval is granted."""
    video = await uow.videos.get_by_id(video_id)
    if video is None:
        raise NotFoundError("Video", video_id)
    if video.status != VideoStatus.DRAFT:
        raise ConflictError("only draft videos can request publish approval")

    now = datetime.now(UTC)
    approval = Approval(
        id=uuid7(),
        kind=ApprovalKind.PUBLISH,
        status=ApprovalStatus.PENDING,
        payload={"video_id": str(video_id)},
        requested_by_user_id=requested_by_user_id,
        created_at=now,
        updated_at=now,
    )
    await uow.approvals.add(approval)
    await uow.commit()
    return approval
