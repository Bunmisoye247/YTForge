from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from uuid6 import uuid7

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Voiceover


@dataclass(frozen=True, slots=True)
class AddVoiceoverInput:
    project_id: uuid.UUID
    asset_id: uuid.UUID
    transcript: str
    duration_seconds: Decimal
    scene_id: uuid.UUID | None = None
    voice_profile_id: uuid.UUID | None = None
    word_timestamps: list[Any] = field(default_factory=list)


async def add_voiceover(uow: UnitOfWork, data: AddVoiceoverInput) -> Voiceover:
    if await uow.projects.get_by_id(data.project_id) is None:
        raise NotFoundError("Project", data.project_id)
    if await uow.assets.get_by_id(data.asset_id) is None:
        raise NotFoundError("Asset", data.asset_id)

    now = datetime.now(UTC)
    voiceover = Voiceover(
        id=uuid7(),
        project_id=data.project_id,
        scene_id=data.scene_id,
        voice_profile_id=data.voice_profile_id,
        asset_id=data.asset_id,
        transcript=data.transcript,
        duration_seconds=data.duration_seconds,
        word_timestamps=data.word_timestamps,
        created_at=now,
        updated_at=now,
    )
    await uow.voiceovers.add(voiceover)
    await uow.commit()
    return voiceover
