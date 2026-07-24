from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from ytforge.domain.enums import JobStatus


@dataclass(slots=True)
class Job:
    id: uuid.UUID
    temporal_workflow_id: str
    temporal_run_id: str
    workflow_type: str
    project_id: uuid.UUID | None
    status: JobStatus
    started_at: datetime
    completed_at: datetime | None = None
    last_heartbeat_at: datetime | None = None
    error: str | None = None
