from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ytforge.domain.enums import VideoStatus


class VideoCreateRequest(BaseModel):
    render_asset_id: uuid.UUID
    title: str = Field(min_length=1, max_length=100)
    description: str
    synthetic_content_disclosure: bool = True


class VideoUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None


class VideoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    render_asset_id: uuid.UUID
    title: str
    description: str
    status: VideoStatus
    synthetic_content_disclosure: bool
    youtube_video_id: str | None
    scheduled_publish_at: datetime | None
    published_at: datetime | None


class SeoMetadataSetRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=5000)
    thumbnail_asset_id: uuid.UUID | None = None
    tags: list[Any] = Field(default_factory=list)
    chapters: list[Any] = Field(default_factory=list)
    keywords: list[Any] = Field(default_factory=list)


class SeoMetadataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    video_id: uuid.UUID
    title: str
    description: str
    thumbnail_asset_id: uuid.UUID | None
    tags: list[Any]
    chapters: list[Any]
    keywords: list[Any]
