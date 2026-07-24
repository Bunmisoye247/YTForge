from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from ytforge.domain.enums import PromptRunStatus


@dataclass(slots=True, kw_only=True)
class PromptTemplate:
    id: uuid.UUID
    agent: str
    name: str
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True, kw_only=True)
class PromptVersion:
    id: uuid.UUID
    template_id: uuid.UUID
    version: int
    content: str
    created_at: datetime
    updated_at: datetime
    front_matter: dict[str, Any] = field(default_factory=dict)
    model_hints: dict[str, Any] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, kw_only=True)
class PromptRun:
    id: uuid.UUID
    prompt_version_id: uuid.UUID
    project_id: uuid.UUID | None
    input_variables: dict[str, Any]
    rendered_prompt: str
    model_used: str
    status: PromptRunStatus
    created_at: datetime
    updated_at: datetime
    response: str | None = None
    latency_ms: int | None = None
    cost_usd: Decimal | None = None
