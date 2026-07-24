from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ytforge.domain.enums import ScriptStatus
from ytforge.domain.errors import InvalidTransitionError

_LEGAL_TRANSITIONS: dict[ScriptStatus, frozenset[ScriptStatus]] = {
    ScriptStatus.DRAFT: frozenset({ScriptStatus.IN_REVIEW}),
    ScriptStatus.IN_REVIEW: frozenset({ScriptStatus.APPROVED, ScriptStatus.REJECTED, ScriptStatus.DRAFT}),
    ScriptStatus.APPROVED: frozenset(),
    ScriptStatus.REJECTED: frozenset({ScriptStatus.DRAFT}),
}


@dataclass(slots=True, kw_only=True)
class Script:
    id: uuid.UUID
    project_id: uuid.UUID
    version: int
    status: ScriptStatus
    created_at: datetime
    updated_at: datetime
    sections: dict[str, Any] = field(default_factory=dict)
    model_used: str | None = None
    token_count: int | None = None

    def transition_to(self, status: ScriptStatus) -> None:
        if status not in _LEGAL_TRANSITIONS[self.status]:
            raise InvalidTransitionError("Script", self.status.value, status.value)
        self.status = status
