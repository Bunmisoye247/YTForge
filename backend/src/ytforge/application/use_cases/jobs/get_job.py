from __future__ import annotations

import uuid

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Job


async def get_job(uow: UnitOfWork, job_id: uuid.UUID) -> Job:
    job = await uow.jobs.get_by_id(job_id)
    if job is None:
        raise NotFoundError("Job", job_id)
    return job
