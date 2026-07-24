from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ytforge.domain.enums import ChannelRole


class ChannelCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    youtube_channel_id: str | None = None
    brand_kit: dict[str, Any] = Field(default_factory=dict)
    defaults: dict[str, Any] = Field(default_factory=dict)


class ChannelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    youtube_channel_id: str | None
    brand_kit: dict[str, Any]
    defaults: dict[str, Any]


class ChannelMemberAddRequest(BaseModel):
    user_id: uuid.UUID
    role: ChannelRole


class ChannelMemberRoleUpdateRequest(BaseModel):
    role: ChannelRole


class ChannelMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    channel_id: uuid.UUID
    user_id: uuid.UUID
    role: ChannelRole
