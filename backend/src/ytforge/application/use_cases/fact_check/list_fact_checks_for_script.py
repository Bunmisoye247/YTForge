from __future__ import annotations

import uuid

from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import FactCheck


async def list_fact_checks_for_script(uow: UnitOfWork, script_id: uuid.UUID) -> list[FactCheck]:
    return await uow.fact_checks.list_for_script(script_id)
