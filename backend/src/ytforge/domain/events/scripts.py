from __future__ import annotations

import uuid
from dataclasses import dataclass

from ytforge.domain.enums import ScriptStatus


@dataclass(frozen=True, slots=True)
class ScriptStatusChanged:
    script_id: uuid.UUID
    from_status: ScriptStatus
    to_status: ScriptStatus
