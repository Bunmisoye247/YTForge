from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class RenderedPrompt:
    content: str
    agent: str
    name: str
    version: int
    model_hints: dict[str, Any] = field(default_factory=dict)
    variables_used: dict[str, Any] = field(default_factory=dict)
