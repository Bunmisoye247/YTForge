from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class VideoRequest:
    prompt: str
    model: str
    duration_seconds: float
    image_reference_key: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


class VideoJobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class VideoJob:
    provider_job_id: str
    model: str
    # Adapters don't know their own registry key — the router stamps this
    # in after `generate()` returns, so `poll_video` knows which provider
    # instance actually owns `provider_job_id` without guessing from `model`.
    provider: str = ""
    # Stamped by the adapter's own `generate()` from the originating
    # VideoRequest — per-second-rate adapters (runway/veo/kling/luma/hailuo)
    # need this in `poll()` to turn a flat per-second rate into an actual
    # cost; it can't be recovered from the provider's job-status response.
    duration_seconds: float = 0.0


@dataclass(frozen=True, slots=True)
class VideoJobStatus:
    state: VideoJobState
    object_key: str | None = None
    latency_ms: int | None = None
    cost_usd: float | None = None
    error: str | None = None
