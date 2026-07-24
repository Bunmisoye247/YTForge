from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ImageRequest:
    prompt: str
    model: str
    negative_prompt: str | None = None
    width: int = 1024
    height: int = 1024
    count: int = 1
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ImageAsset:
    object_key: str
    content_type: str
    model: str
    latency_ms: int
    cost_usd: float | None = None
