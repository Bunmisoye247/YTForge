from __future__ import annotations

import uuid
from typing import Protocol

from ytforge.application.common.pagination import Page, PageParams
from ytforge.domain.entities import Approval
from ytforge.domain.enums import ApprovalStatus


class ApprovalRepository(Protocol):
    async def get_by_id(self, approval_id: uuid.UUID) -> Approval | None: ...
    async def add(self, approval: Approval) -> None: ...
    async def update(self, approval: Approval) -> None: ...
    async def list_by_status(
        self, status: ApprovalStatus | None, params: PageParams
    ) -> Page[Approval]: ...
