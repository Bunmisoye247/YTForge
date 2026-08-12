from __future__ import annotations

from typing import Protocol

from ytforge.application.dto.music import MusicAsset, MusicRequest


class MusicProvider(Protocol):
    async def generate(self, req: MusicRequest) -> MusicAsset: ...
    async def health_check(self) -> None: ...
