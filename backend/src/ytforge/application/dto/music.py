from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class MusicRequest:
    prompt: str
    model: str
    duration_seconds: float
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MusicAsset:
    object_key: str
    content_type: str
    duration_seconds: float
    model: str
    latency_ms: int
    cost_usd: float | None = None
