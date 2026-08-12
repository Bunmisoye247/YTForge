from __future__ import annotations

import hashlib
from urllib.parse import quote

from ytforge.application.dto.image import ImageAsset, ImageRequest
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call


class PollinationsProvider:
    """Pollinations.ai free, keyless image generation API — a synchronous
    GET against `/prompt/{url-encoded prompt}` returns image bytes
    directly, no submit-then-poll job like the paid cloud providers.
    https://pollinations.ai/ An optional registered `token` (their
    referrer/app auth) raises rate limits and drops the default watermark;
    omitting it still works for casual/dev use, which is why `is_configured`
    (ProviderSettings) only needs a non-empty base_url, not an api_key.
    Pollinations has no separate negative-prompt parameter — it's folded
    into the prompt text itself ("... Avoid: {negative}")."""

    def __init__(self, base_url: str, storage: ObjectStorage, bucket: str, api_key: str | None = None) -> None:
        self._client = ProviderHttpClient("pollinations", base_url)
        self._storage = storage
        self._bucket = bucket
        self._api_key = api_key

    async def generate(self, req: ImageRequest) -> list[ImageAsset]:
        async with record_provider_call("pollinations", "image.generate") as metric:
            metric.cost_usd = 0.0
            assets: list[ImageAsset] = []
            for seed in range(req.count):
                object_key = await self._generate_one(req, seed)
                assets.append(
                    ImageAsset(
                        object_key=object_key,
                        content_type="image/jpeg",
                        model=req.model,
                        latency_ms=0,
                        cost_usd=0.0,
                    )
                )
            return assets

    async def _generate_one(self, req: ImageRequest, seed: int) -> str:
        prompt = f"{req.prompt}. Avoid: {req.negative_prompt}" if req.negative_prompt else req.prompt
        path = f"/prompt/{quote(prompt, safe='')}"
        params: dict[str, object] = {
            "width": req.width,
            "height": req.height,
            "model": req.model,
            "seed": seed,
            "nologo": "true",
            **({"token": self._api_key} if self._api_key else {}),
        }
        data = await self._client.get_bytes(path, params)
        digest = hashlib.sha256(data).hexdigest()[:16]
        key = f"pollinations/{digest}.jpg"
        await self._storage.put_object(self._bucket, key, data, "image/jpeg")
        return key

    async def health_check(self) -> None:
        await self._client.ping("/prompt/test", params={"width": 64, "height": 64})
