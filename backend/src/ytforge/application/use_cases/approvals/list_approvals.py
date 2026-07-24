from __future__ import annotations

from ytforge.application.common.pagination import Page, PageParams
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Approval
from ytforge.domain.enums import ApprovalStatus


async def list_approvals(
    uow: UnitOfWork, status: ApprovalStatus | None, params: PageParams
) -> Page[Approval]:
    return await uow.approvals.list_by_status(status, params)
