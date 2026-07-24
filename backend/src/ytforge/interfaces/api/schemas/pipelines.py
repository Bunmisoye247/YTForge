from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ytforge.domain.enums import JobStatus


class StartPipelineRequest(BaseModel):
    project_id: uuid.UUID
    topic: str


class StartPipelineResponse(BaseModel):
    workflow_id: str
    run_id: str


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    temporal_workflow_id: str
    temporal_run_id: str
    workflow_type: str
    project_id: uuid.UUID | None
    status: JobStatus
    started_at: datetime
    completed_at: datetime | None
    last_heartbeat_at: datetime | None
    error: str | None
