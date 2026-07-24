from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from uuid6 import uuid7

from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Job
from ytforge.domain.enums import JobStatus


@dataclass(frozen=True, slots=True)
class RecordJobStartedInput:
    temporal_workflow_id: str
    temporal_run_id: str
    workflow_type: str
    project_id: uuid.UUID | None = None


async def record_job_started(uow: UnitOfWork, data: RecordJobStartedInput) -> Job:
    """Called from a Temporal activity right after a workflow starts — the
    `jobs` table mirrors Temporal run state for dashboard queries
    (ARCHITECTURE.md §6.1) without the dashboard needing to talk to
    Temporal directly."""
    now = datetime.now(UTC)
    job = Job(
        id=uuid7(),
        temporal_workflow_id=data.temporal_workflow_id,
        temporal_run_id=data.temporal_run_id,
        workflow_type=data.workflow_type,
        project_id=data.project_id,
        status=JobStatus.RUNNING,
        started_at=now,
    )
    await uow.jobs.add(job)
    await uow.commit()
    return job
