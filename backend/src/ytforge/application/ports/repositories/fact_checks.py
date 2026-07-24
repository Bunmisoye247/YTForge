from __future__ import annotations

import uuid
from typing import Protocol

from ytforge.domain.entities import FactCheck


class FactCheckRepository(Protocol):
    async def add(self, fact_check: FactCheck) -> None: ...
    async def list_for_script(self, script_id: uuid.UUID) -> list[FactCheck]: ...
