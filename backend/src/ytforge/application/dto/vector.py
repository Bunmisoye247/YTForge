from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

Vector = list[float]


@dataclass(frozen=True, slots=True)
class VectorPoint:
    id: str
    vector: Vector
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VectorMatch:
    id: str
    score: float
    payload: dict[str, Any] = field(default_factory=dict)
