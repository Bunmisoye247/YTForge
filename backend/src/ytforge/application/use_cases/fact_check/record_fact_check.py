from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from uuid6 import uuid7

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import FactCheck
from ytforge.domain.enums import FactCheckVerdict


@dataclass(frozen=True, slots=True)
class RecordFactCheckInput:
    script_id: uuid.UUID
    verdict: FactCheckVerdict
    flags: list[Any] = field(default_factory=list)
    model_used: str | None = None


async def record_fact_check(uow: UnitOfWork, data: RecordFactCheckInput) -> FactCheck:
    script = await uow.scripts.get_by_id(data.script_id)
    if script is None:
        raise NotFoundError("Script", data.script_id)

    now = datetime.now(UTC)
    fact_check = FactCheck(
        id=uuid7(),
        script_id=data.script_id,
        script_version=script.version,
        verdict=data.verdict,
        flags=data.flags,
        model_used=data.model_used,
        created_at=now,
        updated_at=now,
    )
    await uow.fact_checks.add(fact_check)
    await uow.commit()
    return fact_check
