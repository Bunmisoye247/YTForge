from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ytforge.domain.enums import ApprovalKind, ApprovalStatus


class ApprovalRequestRequest(BaseModel):
    kind: ApprovalKind
    payload: dict[str, Any] = Field(default_factory=dict)
    workflow_id: str | None = None


class ApprovalDecisionRequest(BaseModel):
    status: ApprovalStatus
    note: str | None = None


class ApprovalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: ApprovalKind
    status: ApprovalStatus
    payload: dict[str, Any]
    workflow_id: str | None
    requested_by_user_id: uuid.UUID | None
    decided_by_user_id: uuid.UUID | None
    decided_at: datetime | None
    note: str | None
