from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from uuid6 import uuid7

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import VoiceProfile
from ytforge.domain.enums import VoiceProfileStatus


@dataclass(frozen=True, slots=True)
class RegisterVoiceProfileInput:
    channel_id: uuid.UUID
    name: str
    provider: str
    provider_voice_id: str
    consent_artifact_object_key: str
    consent_recorded_at: datetime


async def register_voice_profile(uow: UnitOfWork, data: RegisterVoiceProfileInput) -> VoiceProfile:
    if await uow.channels.get_by_id(data.channel_id) is None:
        raise NotFoundError("Channel", data.channel_id)

    now = datetime.now(UTC)
    profile = VoiceProfile(
        id=uuid7(),
        channel_id=data.channel_id,
        name=data.name,
        provider=data.provider,
        provider_voice_id=data.provider_voice_id,
        status=VoiceProfileStatus.PENDING_APPROVAL,
        consent_artifact_object_key=data.consent_artifact_object_key,
        consent_recorded_at=data.consent_recorded_at,
        created_at=now,
        updated_at=now,
    )
    await uow.voice_profiles.add(profile)
    await uow.commit()
    return profile
