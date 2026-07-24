from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ytforge.domain.enums import VoiceProfileStatus


class VoiceCloneRequestRequest(BaseModel):
    proposed_name: str = Field(min_length=1, max_length=255)
    consent_artifact_object_key: str = Field(min_length=1, max_length=1024)


class VoiceProfileRegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    provider: str = Field(min_length=1, max_length=64)
    provider_voice_id: str = Field(min_length=1, max_length=255)
    consent_artifact_object_key: str = Field(min_length=1, max_length=1024)
    consent_recorded_at: datetime


class VoiceProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    channel_id: uuid.UUID
    name: str
    provider: str
    provider_voice_id: str
    status: VoiceProfileStatus
    consent_artifact_object_key: str
    consent_recorded_at: datetime


class VoiceoverCreateRequest(BaseModel):
    asset_id: uuid.UUID
    transcript: str = Field(min_length=1)
    duration_seconds: Decimal = Field(gt=0)
    scene_id: uuid.UUID | None = None
    voice_profile_id: uuid.UUID | None = None
    word_timestamps: list[Any] = Field(default_factory=list)


class VoiceoverRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    scene_id: uuid.UUID | None
    voice_profile_id: uuid.UUID | None
    asset_id: uuid.UUID
    transcript: str
    duration_seconds: Decimal
    word_timestamps: list[Any]
