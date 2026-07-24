from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from ytforge.domain.enums import StoryboardStatus


class StoryboardCreateRequest(BaseModel):
    script_id: uuid.UUID


class StoryboardStatusUpdateRequest(BaseModel):
    status: StoryboardStatus


class StoryboardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    script_id: uuid.UUID
    status: StoryboardStatus


class SceneCreateRequest(BaseModel):
    sequence_index: int = Field(ge=0)
    description: str = Field(min_length=1)
    duration_seconds: Decimal = Field(gt=0)
    image_prompt: str | None = None
    video_prompt: str | None = None
    voice_line: str | None = None


class SceneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    storyboard_id: uuid.UUID
    sequence_index: int
    description: str
    duration_seconds: Decimal
    image_prompt: str | None
    video_prompt: str | None
    voice_line: str | None


class SceneReorderRequest(BaseModel):
    ordered_scene_ids: list[uuid.UUID]
