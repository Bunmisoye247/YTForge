from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from uuid6 import uuid7

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Project
from ytforge.domain.enums import ProjectStatus


@dataclass(frozen=True, slots=True)
class CreateProjectInput:
    channel_id: uuid.UUID
    title: str
    created_by_user_id: uuid.UUID | None = None
    trend_id: uuid.UUID | None = None
    budget_usd: Decimal | None = None


async def create_project(uow: UnitOfWork, data: CreateProjectInput) -> Project:
    if await uow.channels.get_by_id(data.channel_id) is None:
        raise NotFoundError("Channel", data.channel_id)

    now = datetime.now(UTC)
    project = Project(
        id=uuid7(),
        channel_id=data.channel_id,
        trend_id=data.trend_id,
        created_by_user_id=data.created_by_user_id,
        title=data.title,
        status=ProjectStatus.IDEA,
        budget_usd=data.budget_usd,
        created_at=now,
        updated_at=now,
    )
    await uow.projects.add(project)
    await uow.commit()
    return project
