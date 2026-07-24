from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ytforge.domain.enums import FactCheckVerdict, ScriptStatus


class ScriptCreateRequest(BaseModel):
    sections: dict[str, Any] = Field(default_factory=dict)
    model_used: str | None = None
    token_count: int | None = None


class ScriptStatusUpdateRequest(BaseModel):
    status: ScriptStatus


class ScriptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    version: int
    status: ScriptStatus
    sections: dict[str, Any]
    model_used: str | None
    token_count: int | None


class FactCheckCreateRequest(BaseModel):
    verdict: FactCheckVerdict
    flags: list[Any] = Field(default_factory=list)
    model_used: str | None = None


class FactCheckRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    script_id: uuid.UUID
    script_version: int
    verdict: FactCheckVerdict
    flags: list[Any]
    model_used: str | None
