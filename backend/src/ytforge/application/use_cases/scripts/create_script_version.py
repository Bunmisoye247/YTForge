from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from uuid6 import uuid7

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Script
from ytforge.domain.enums import ScriptStatus


@dataclass(frozen=True, slots=True)
class CreateScriptVersionInput:
    project_id: uuid.UUID
    sections: dict[str, Any] = field(default_factory=dict)
    model_used: str | None = None
    token_count: int | None = None


async def create_script_version(uow: UnitOfWork, data: CreateScriptVersionInput) -> Script:
    """Scripts are never edited in place — each call appends a new version."""
    if await uow.projects.get_by_id(data.project_id) is None:
        raise NotFoundError("Project", data.project_id)

    latest = await uow.scripts.get_latest_for_project(data.project_id)
    next_version = 1 if latest is None else latest.version + 1

    now = datetime.now(UTC)
    script = Script(
        id=uuid7(),
        project_id=data.project_id,
        version=next_version,
        status=ScriptStatus.DRAFT,
        sections=data.sections,
        model_used=data.model_used,
        token_count=data.token_count,
        created_at=now,
        updated_at=now,
    )
    await uow.scripts.add(script)
    await uow.commit()
    return script
