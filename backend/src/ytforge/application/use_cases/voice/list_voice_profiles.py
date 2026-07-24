from __future__ import annotations

import uuid

from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Voiceover, VoiceProfile


async def list_voice_profiles(uow: UnitOfWork, channel_id: uuid.UUID) -> list[VoiceProfile]:
    return await uow.voice_profiles.list_for_channel(channel_id)


async def list_voiceovers(uow: UnitOfWork, project_id: uuid.UUID) -> list[Voiceover]:
    return await uow.voiceovers.list_for_project(project_id)
