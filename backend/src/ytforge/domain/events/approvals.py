from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApprovalGranted:
    approval_id: uuid.UUID
    decided_by_user_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class ApprovalRejected:
    approval_id: uuid.UUID
    decided_by_user_id: uuid.UUID
