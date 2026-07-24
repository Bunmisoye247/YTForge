from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from uuid6 import uuid7

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Scene


@dataclass(frozen=True, slots=True)
class AddSceneInput:
    storyboard_id: uuid.UUID
    sequence_index: int
    description: str
    duration_seconds: Decimal
    image_prompt: str | None = None
    video_prompt: str | None = None
    voice_line: str | None = None


async def add_scene(uow: UnitOfWork, data: AddSceneInput) -> Scene:
    if await uow.storyboards.get_by_id(data.storyboard_id) is None:
        raise NotFoundError("Storyboard", data.storyboard_id)

    now = datetime.now(UTC)
    scene = Scene(
        id=uuid7(),
        storyboard_id=data.storyboard_id,
        sequence_index=data.sequence_index,
        description=data.description,
        duration_seconds=data.duration_seconds,
        image_prompt=data.image_prompt,
        video_prompt=data.video_prompt,
        voice_line=data.voice_line,
        created_at=now,
        updated_at=now,
    )
    await uow.scenes.add(scene)
    await uow.commit()
    return scene
