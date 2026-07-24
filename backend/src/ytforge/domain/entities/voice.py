from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from ytforge.domain.enums import VoiceProfileStatus
from ytforge.domain.errors import InvalidTransitionError

_LEGAL_TRANSITIONS: dict[VoiceProfileStatus, frozenset[VoiceProfileStatus]] = {
    VoiceProfileStatus.PENDING_APPROVAL: frozenset({VoiceProfileStatus.APPROVED, VoiceProfileStatus.REVOKED}),
    VoiceProfileStatus.APPROVED: frozenset({VoiceProfileStatus.REVOKED}),
    VoiceProfileStatus.REVOKED: frozenset(),
}


@dataclass(slots=True, kw_only=True)
class VoiceProfile:
    id: uuid.UUID
    channel_id: uuid.UUID
    name: str
    provider: str
    provider_voice_id: str
    status: VoiceProfileStatus
    consent_artifact_object_key: str
    consent_recorded_at: datetime
    created_at: datetime
    updated_at: datetime

    def approve(self) -> None:
        self._transition(VoiceProfileStatus.APPROVED)

    def revoke(self) -> None:
        self._transition(VoiceProfileStatus.REVOKED)

    def _transition(self, status: VoiceProfileStatus) -> None:
        if status not in _LEGAL_TRANSITIONS[self.status]:
            raise InvalidTransitionError("VoiceProfile", self.status.value, status.value)
        self.status = status


@dataclass(slots=True, kw_only=True)
class Voiceover:
    id: uuid.UUID
    project_id: uuid.UUID
    scene_id: uuid.UUID | None
    voice_profile_id: uuid.UUID | None
    asset_id: uuid.UUID
    transcript: str
    duration_seconds: Decimal
    created_at: datetime
    updated_at: datetime
    word_timestamps: list[Any] = field(default_factory=list)
