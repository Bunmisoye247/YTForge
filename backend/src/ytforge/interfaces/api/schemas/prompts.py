from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ytforge.domain.enums import PromptRunStatus


class PromptTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent: str
    name: str


class PromptVersionCreateRequest(BaseModel):
    agent: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    front_matter: dict[str, Any] = Field(default_factory=dict)
    model_hints: dict[str, Any] = Field(default_factory=dict)
    variables: dict[str, Any] = Field(default_factory=dict)


class PromptVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    template_id: uuid.UUID
    version: int
    content: str
    front_matter: dict[str, Any]
    model_hints: dict[str, Any]
    variables: dict[str, Any]


class PromptRunCreateRequest(BaseModel):
    prompt_version_id: uuid.UUID
    input_variables: dict[str, Any]
    rendered_prompt: str
    model_used: str
    status: PromptRunStatus
    project_id: uuid.UUID | None = None
    response: str | None = None
    latency_ms: int | None = None
    cost_usd: Decimal | None = None


class PromptRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    prompt_version_id: uuid.UUID
    project_id: uuid.UUID | None
    input_variables: dict[str, Any]
    rendered_prompt: str
    model_used: str
    status: PromptRunStatus
    response: str | None
    latency_ms: int | None
    cost_usd: Decimal | None
