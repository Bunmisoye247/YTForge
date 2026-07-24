from __future__ import annotations

import base64
import hashlib

from ytforge.application.dto.image import ImageAsset, ImageRequest
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call


class SdxlDiffusersProvider:
    """Local SDXL server (a HuggingFace `diffusers` pipeline exposed over
    HTTP, e.g. via a small FastAPI wrapper) rather than in-process model
    loading — keeps this adapter dependency-free of torch/diffusers, which
    would otherwise be a mandatory multi-GB install for every environment
    regardless of whether local image gen is used.
    # verify request/response shape against your actual server wrapper."""

    def __init__(self, base_url: str, storage: ObjectStorage, bucket: str) -> None:
        self._client = ProviderHttpClient("sdxl_diffusers", base_url)
        self._storage = storage
        self._bucket = bucket

    async def generate(self, req: ImageRequest) -> list[ImageAsset]:
        async with record_provider_call("sdxl_diffusers", "image.generate") as metric:
            body = await self._client.post_json(
                "/generate",
                {
                    "prompt": req.prompt,
                    "negative_prompt": req.negative_prompt or "",
                    "width": req.width,
                    "height": req.height,
                    "num_images": req.count,
                    "model": req.model,
                },
            )
            metric.cost_usd = 0.0
            assets = []
            for image_b64 in body["images"]:
                raw = base64.b64decode(image_b64)
                digest = hashlib.sha256(raw).hexdigest()[:16]
                key = f"sdxl/{digest}.png"
                await self._storage.put_object(self._bucket, key, raw, "image/png")
                assets.append(
                    ImageAsset(object_key=key, content_type="image/png", model=req.model, latency_ms=0, cost_usd=0.0)
                )
            return assets
