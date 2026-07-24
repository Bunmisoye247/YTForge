from __future__ import annotations

import base64
import hashlib

from ytforge.application.dto.image import ImageAsset, ImageRequest
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call


class A1111Provider:
    """Local AUTOMATIC1111 Stable Diffusion WebUI REST API.
    https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API
    Free/local — cost is always 0. Reference pattern (Phase 7) for
    synchronous-bytes adapters: the provider returns bytes inline (here,
    base64 in the JSON body), so this adapter uploads them to object
    storage itself and returns the REAL key — never a placeholder — since
    ARCHITECTURE.md §6.3 requires every `Asset.object_key` to resolve to
    something this app controls."""

    def __init__(self, base_url: str, storage: ObjectStorage, bucket: str) -> None:
        self._client = ProviderHttpClient("a1111", base_url)
        self._storage = storage
        self._bucket = bucket

    async def generate(self, req: ImageRequest) -> list[ImageAsset]:
        async with record_provider_call("a1111", "image.generate") as metric:
            body = await self._client.post_json(
                "/sdapi/v1/txt2img",
                {
                    "prompt": req.prompt,
                    "negative_prompt": req.negative_prompt or "",
                    "width": req.width,
                    "height": req.height,
                    "batch_size": req.count,
                    "override_settings": {"sd_model_checkpoint": req.model},
                },
            )
            metric.cost_usd = 0.0
            assets = []
            for image_b64 in body["images"]:
                raw = base64.b64decode(image_b64)
                digest = hashlib.sha256(raw).hexdigest()[:16]
                key = f"a1111/{digest}.png"
                await self._storage.put_object(self._bucket, key, raw, "image/png")
                assets.append(
                    ImageAsset(object_key=key, content_type="image/png", model=req.model, latency_ms=0, cost_usd=0.0)
                )
            return assets
