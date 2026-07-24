from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Job
from ytforge.domain.enums import JobStatus

_TERMINAL_STATUSES = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.TERMINATED, JobStatus.TIMED_OUT, JobStatus.CANCELLED}


async def update_job_status(
    uow: UnitOfWork, job_id: uuid.UUID, status: JobStatus, error: str | None = None
) -> Job:
    job = await uow.jobs.get_by_id(job_id)
    if job is None:
        raise NotFoundError("Job", job_id)

    job.status = status
    job.error = error
    if status in _TERMINAL_STATUSES:
        job.completed_at = datetime.now(UTC)
    await uow.jobs.update(job)
    await uow.commit()
    return job
