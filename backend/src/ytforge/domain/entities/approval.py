from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ytforge.domain.enums import ApprovalKind, ApprovalStatus
from ytforge.domain.errors import InvalidTransitionError


@dataclass(slots=True, kw_only=True)
class Approval:
    id: uuid.UUID
    kind: ApprovalKind
    status: ApprovalStatus
    created_at: datetime
    updated_at: datetime
    payload: dict[str, Any] = field(default_factory=dict)
    workflow_id: str | None = None
    requested_by_user_id: uuid.UUID | None = None
    decided_by_user_id: uuid.UUID | None = None
    decided_at: datetime | None = None
    note: str | None = None

    def decide(
        self,
        *,
        status: ApprovalStatus,
        decided_by_user_id: uuid.UUID,
        decided_at: datetime,
        note: str | None = None,
    ) -> None:
        if self.status != ApprovalStatus.PENDING or status == ApprovalStatus.PENDING:
            raise InvalidTransitionError("Approval", self.status.value, status.value)
        self.status = status
        self.decided_by_user_id = decided_by_user_id
        self.decided_at = decided_at
        self.note = note
