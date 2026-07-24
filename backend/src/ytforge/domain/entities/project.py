from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from ytforge.domain.enums import ProjectStatus
from ytforge.domain.errors import InvalidTransitionError

_LEGAL_TRANSITIONS: dict[ProjectStatus, frozenset[ProjectStatus]] = {
    ProjectStatus.IDEA: frozenset({ProjectStatus.IN_PROGRESS, ProjectStatus.ARCHIVED}),
    ProjectStatus.IN_PROGRESS: frozenset({ProjectStatus.IN_REVIEW, ProjectStatus.ARCHIVED}),
    ProjectStatus.IN_REVIEW: frozenset(
        {ProjectStatus.IN_PROGRESS, ProjectStatus.COMPLETED, ProjectStatus.ARCHIVED}
    ),
    ProjectStatus.COMPLETED: frozenset({ProjectStatus.ARCHIVED}),
    ProjectStatus.ARCHIVED: frozenset(),
}


@dataclass(slots=True, kw_only=True)
class Project:
    id: uuid.UUID
    channel_id: uuid.UUID
    trend_id: uuid.UUID | None
    created_by_user_id: uuid.UUID | None
    title: str
    status: ProjectStatus
    budget_usd: Decimal | None
    created_at: datetime
    updated_at: datetime

    def transition_to(self, status: ProjectStatus) -> None:
        if status not in _LEGAL_TRANSITIONS[self.status]:
            raise InvalidTransitionError("Project", self.status.value, status.value)
        self.status = status
