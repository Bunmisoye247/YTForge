from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.application.common.pagination import Page, PageParams
from ytforge.domain.entities import Job
from ytforge.infrastructure.db.models import Job as JobOrm
from ytforge.infrastructure.db.repositories._pagination import paginate


def _to_domain(row: JobOrm) -> Job:
    return Job(
        id=row.id,
        temporal_workflow_id=row.temporal_workflow_id,
        temporal_run_id=row.temporal_run_id,
        workflow_type=row.workflow_type,
        project_id=row.project_id,
        status=row.status,
        started_at=row.started_at,
        completed_at=row.completed_at,
        last_heartbeat_at=row.last_heartbeat_at,
        error=row.error,
    )


class SqlAlchemyJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, job_id: uuid.UUID) -> Job | None:
        row = await self._session.get(JobOrm, job_id)
        return _to_domain(row) if row is not None else None

    async def list_for_project(
        self, project_id: uuid.UUID | None, params: PageParams
    ) -> Page[Job]:
        stmt = select(JobOrm).order_by(JobOrm.started_at.desc())
        if project_id is not None:
            stmt = stmt.where(JobOrm.project_id == project_id)
        return await paginate(self._session, stmt, params, _to_domain)

    async def add(self, job: Job) -> None:
        self._session.add(
            JobOrm(
                id=job.id,
                temporal_workflow_id=job.temporal_workflow_id,
                temporal_run_id=job.temporal_run_id,
                workflow_type=job.workflow_type,
                project_id=job.project_id,
                status=job.status,
                started_at=job.started_at,
                completed_at=job.completed_at,
                last_heartbeat_at=job.last_heartbeat_at,
                error=job.error,
            )
        )
        await self._session.flush()

    async def update(self, job: Job) -> None:
        row = await self._session.get(JobOrm, job.id)
        assert row is not None
        row.status = job.status
        row.completed_at = job.completed_at
        row.last_heartbeat_at = job.last_heartbeat_at
        row.error = job.error
        await self._session.flush()
