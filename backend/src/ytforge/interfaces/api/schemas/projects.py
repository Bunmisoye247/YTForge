from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from ytforge.domain.enums import ProjectStatus


class ProjectCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    trend_id: uuid.UUID | None = None
    budget_usd: Decimal | None = None


class ProjectUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    budget_usd: Decimal | None = None


class ProjectStatusUpdateRequest(BaseModel):
    status: ProjectStatus


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    channel_id: uuid.UUID
    trend_id: uuid.UUID | None
    created_by_user_id: uuid.UUID | None
    title: str
    status: ProjectStatus
    budget_usd: Decimal | None
