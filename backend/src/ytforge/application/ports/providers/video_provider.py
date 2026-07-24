from __future__ import annotations

from typing import Protocol

from ytforge.application.dto.video import VideoJob, VideoJobStatus, VideoRequest


class VideoProvider(Protocol):
    async def generate(self, req: VideoRequest) -> VideoJob: ...
    async def poll(self, job: VideoJob) -> VideoJobStatus: ...
