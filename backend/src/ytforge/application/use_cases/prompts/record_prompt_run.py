from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from uuid6 import uuid7

from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import PromptRun
from ytforge.domain.enums import PromptRunStatus


@dataclass(frozen=True, slots=True)
class RecordPromptRunInput:
    prompt_version_id: uuid.UUID
    input_variables: dict[str, Any]
    rendered_prompt: str
    model_used: str
    status: PromptRunStatus
    project_id: uuid.UUID | None = None
    response: str | None = None
    latency_ms: int | None = None
    cost_usd: Decimal | None = None


async def record_prompt_run(uow: UnitOfWork, data: RecordPromptRunInput) -> PromptRun:
    run = PromptRun(
        id=uuid7(),
        prompt_version_id=data.prompt_version_id,
        project_id=data.project_id,
        input_variables=data.input_variables,
        rendered_prompt=data.rendered_prompt,
        response=data.response,
        model_used=data.model_used,
        status=data.status,
        latency_ms=data.latency_ms,
        cost_usd=data.cost_usd,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    await uow.prompt_runs.add(run)
    await uow.commit()
    return run
