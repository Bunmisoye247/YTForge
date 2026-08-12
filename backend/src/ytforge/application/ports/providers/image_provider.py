from __future__ import annotations

from typing import Protocol

from ytforge.application.dto.image import ImageAsset, ImageRequest


class ImageProvider(Protocol):
    async def generate(self, req: ImageRequest) -> list[ImageAsset]: ...
    async def health_check(self) -> None: ...
