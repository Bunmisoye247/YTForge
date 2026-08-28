from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class EditingSceneInput:
    scene_id: str
    sequence_index: int
    visual_object_key: str
    voice_object_key: str | None
    duration_seconds: float
    transcript: str | None = None
    word_timestamps: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class EditingRequest:
    project_id: str
    scenes: list[EditingSceneInput]
    music_object_key: str | None = None
    caption_burn_in: bool = True
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EditingResult:
    render_object_key: str
    duration_seconds: float
