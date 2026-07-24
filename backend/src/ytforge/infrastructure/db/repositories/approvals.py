from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.application.common.pagination import Page, PageParams
from ytforge.domain.entities import Approval
from ytforge.domain.enums import ApprovalStatus
from ytforge.infrastructure.db.models import Approval as ApprovalOrm
from ytforge.infrastructure.db.repositories._pagination import paginate


def _to_domain(row: ApprovalOrm) -> Approval:
    return Approval(
        id=row.id,
        kind=row.kind,
        status=row.status,
        payload=row.payload,
        workflow_id=row.workflow_id,
        requested_by_user_id=row.requested_by_user_id,
        decided_by_user_id=row.decided_by_user_id,
        decided_at=row.decided_at,
        note=row.note,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyApprovalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, approval_id: uuid.UUID) -> Approval | None:
        row = await self._session.get(ApprovalOrm, approval_id)
        return _to_domain(row) if row is not None else None

    async def add(self, approval: Approval) -> None:
        row = ApprovalOrm(
            id=approval.id,
            kind=approval.kind,
            status=approval.status,
            payload=approval.payload,
            workflow_id=approval.workflow_id,
            requested_by_user_id=approval.requested_by_user_id,
            decided_by_user_id=approval.decided_by_user_id,
            decided_at=approval.decided_at,
            note=approval.note,
            created_at=approval.created_at,
            updated_at=approval.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def update(self, approval: Approval) -> None:
        row = await self._session.get(ApprovalOrm, approval.id)
        assert row is not None
        row.status = approval.status
        row.decided_by_user_id = approval.decided_by_user_id
        row.decided_at = approval.decided_at
        row.note = approval.note
        row.updated_at = approval.updated_at
        await self._session.flush()

    async def list_by_status(
        self, status: ApprovalStatus | None, params: PageParams
    ) -> Page[Approval]:
        stmt = select(ApprovalOrm).order_by(ApprovalOrm.created_at.desc())
        if status is not None:
            stmt = stmt.where(ApprovalOrm.status == status)
        return await paginate(self._session, stmt, params, _to_domain)
