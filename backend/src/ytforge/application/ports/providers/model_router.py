from __future__ import annotations

from typing import Protocol

from ytforge.application.dto.image import ImageAsset, ImageRequest
from ytforge.application.dto.llm import LLMRequest, LLMResponse
from ytforge.application.dto.music import MusicAsset, MusicRequest
from ytforge.application.dto.tts import AudioAsset, TTSRequest
from ytforge.application.dto.vector import Vector
from ytforge.application.dto.video import VideoJob, VideoJobStatus, VideoRequest


class ModelRouter(Protocol):
    """Resolves a config-driven `route_name` (e.g. "script_writing") to a
    `primary` provider/model, trying `fallback` entries in order on
    failure (ARCHITECTURE.md §4.3). One method per provider capability —
    the route's configured strings determine which provider gets picked,
    the caller just names the route it wants routed."""

    async def complete(self, route_name: str, req: LLMRequest) -> LLMResponse: ...
    async def embed(self, route_name: str, texts: list[str]) -> list[Vector]: ...
    async def generate_image(self, route_name: str, req: ImageRequest) -> list[ImageAsset]: ...
    async def generate_video(self, route_name: str, req: VideoRequest) -> VideoJob: ...
    async def poll_video(self, route_name: str, job: VideoJob) -> VideoJobStatus: ...
    async def synthesize_speech(self, route_name: str, req: TTSRequest) -> AudioAsset: ...
    async def generate_music(self, route_name: str, req: MusicRequest) -> MusicAsset: ...
