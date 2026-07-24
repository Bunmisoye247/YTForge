from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from ytforge.domain.enums import StoryboardStatus
from ytforge.domain.errors import InvalidTransitionError

_LEGAL_TRANSITIONS: dict[StoryboardStatus, frozenset[StoryboardStatus]] = {
    StoryboardStatus.DRAFT: frozenset({StoryboardStatus.READY}),
    StoryboardStatus.READY: frozenset({StoryboardStatus.APPROVED, StoryboardStatus.DRAFT}),
    StoryboardStatus.APPROVED: frozenset(),
}


@dataclass(slots=True, kw_only=True)
class Storyboard:
    id: uuid.UUID
    project_id: uuid.UUID
    script_id: uuid.UUID
    status: StoryboardStatus
    created_at: datetime
    updated_at: datetime

    def transition_to(self, status: StoryboardStatus) -> None:
        if status not in _LEGAL_TRANSITIONS[self.status]:
            raise InvalidTransitionError("Storyboard", self.status.value, status.value)
        self.status = status


@dataclass(slots=True, kw_only=True)
class Scene:
    id: uuid.UUID
    storyboard_id: uuid.UUID
    sequence_index: int
    description: str
    duration_seconds: Decimal
    created_at: datetime
    updated_at: datetime
    image_prompt: str | None = None
    video_prompt: str | None = None
    voice_line: str | None = None
