from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ytforge.application.common.errors import InvalidStateError, NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import VoiceProfile
from ytforge.domain.errors import InvalidTransitionError


async def approve_voice_profile(uow: UnitOfWork, voice_profile_id: uuid.UUID) -> VoiceProfile:
    profile = await uow.voice_profiles.get_by_id(voice_profile_id)
    if profile is None:
        raise NotFoundError("VoiceProfile", voice_profile_id)

    try:
        profile.approve()
    except InvalidTransitionError as exc:
        raise InvalidStateError(exc) from exc
    profile.updated_at = datetime.now(UTC)

    await uow.voice_profiles.update(profile)
    await uow.add_event(
        aggregate_type="voice_profile",
        aggregate_id=profile.id,
        event_type="VoiceProfileApproved",
        payload={},
    )
    await uow.commit()
    return profile
