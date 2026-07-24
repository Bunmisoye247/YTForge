from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from uuid6 import uuid7

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Approval
from ytforge.domain.enums import ApprovalKind, ApprovalStatus


@dataclass(frozen=True, slots=True)
class RequestVoiceCloneInput:
    channel_id: uuid.UUID
    proposed_name: str
    consent_artifact_object_key: str
    requested_by_user_id: uuid.UUID


async def request_voice_clone(uow: UnitOfWork, data: RequestVoiceCloneInput) -> Approval:
    """Records the approval required before any provider clone_voice() call
    (ARCHITECTURE.md §8). The provider call itself is made by Phase-6 code
    once this approval is granted, which then registers the resulting
    VoiceProfile via `register_voice_profile`."""
    if await uow.channels.get_by_id(data.channel_id) is None:
        raise NotFoundError("Channel", data.channel_id)

    now = datetime.now(UTC)
    approval = Approval(
        id=uuid7(),
        kind=ApprovalKind.VOICE_CLONING,
        status=ApprovalStatus.PENDING,
        payload={
            "channel_id": str(data.channel_id),
            "proposed_name": data.proposed_name,
            "consent_artifact_object_key": data.consent_artifact_object_key,
        },
        requested_by_user_id=data.requested_by_user_id,
        created_at=now,
        updated_at=now,
    )
    await uow.approvals.add(approval)
    await uow.commit()
    return approval
