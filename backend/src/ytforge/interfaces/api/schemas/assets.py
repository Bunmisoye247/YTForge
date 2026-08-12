from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ytforge.domain.enums import AssetStatus, AssetType


class AssetRegisterRequest(BaseModel):
    asset_type: AssetType
    bucket: str = Field(min_length=1, max_length=63)
    object_key: str = Field(min_length=1, max_length=1024)
    scene_id: uuid.UUID | None = None
    checksum_sha256: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    scene_id: uuid.UUID | None
    asset_type: AssetType
    status: AssetStatus
    bucket: str
    object_key: str
    checksum_sha256: str | None
    provenance: dict[str, Any]


class PresignedUrlRead(BaseModel):
    url: str
