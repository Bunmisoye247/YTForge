from __future__ import annotations

import asyncio
import hashlib

import httpx

from ytforge.application.dto.image import ImageAsset, ImageRequest
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.errors import ProviderRequestError
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_BASE_URL = "https://api.bfl.ml/v1"
_POLL_INTERVAL_S = 2.0
_POLL_TIMEOUT_S = 120.0


class FluxApiProvider:
    """Black Forest Labs Flux API — async submit-then-poll job pattern.
    https://docs.bfl.ml/ # verify against current provider docs.

    The poll result is a URL hosted on BFL's own CDN — downloaded and
    re-uploaded into our object storage (ARCHITECTURE.md §6.3) rather than
    returned as-is."""

    def __init__(self, api_key: str, storage: ObjectStorage, bucket: str, cost_per_image_usd: float | None = None) -> None:
        self._client = ProviderHttpClient("flux_api", _BASE_URL, {"x-key": api_key})
        self._storage = storage
        self._bucket = bucket
        self._cost_per_image = cost_per_image_usd

    async def generate(self, req: ImageRequest) -> list[ImageAsset]:
        async with record_provider_call("flux_api", "image.generate") as metric:
            assets: list[ImageAsset] = []
            for _ in range(req.count):
                submit = await self._client.post_json(
                    f"/{req.model}",
                    {
                        "prompt": req.prompt,
                        "width": req.width,
                        "height": req.height,
                        **({"negative_prompt": req.negative_prompt} if req.negative_prompt else {}),
                    },
                )
                request_id = submit["id"]
                result_url = await self._poll(request_id)
                object_key = await self._download_and_store(result_url)
                assets.append(
                    ImageAsset(
                        object_key=object_key,
                        content_type="image/png",
                        model=req.model,
                        latency_ms=0,
                        cost_usd=self._cost_per_image,
                    )
                )
            metric.cost_usd = (self._cost_per_image or 0.0) * req.count
            return assets

    async def _download_and_store(self, result_url: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(result_url, timeout=httpx.Timeout(connect=5.0, read=60.0, write=30.0, pool=5.0))
            response.raise_for_status()
            data = response.content
        digest = hashlib.sha256(data).hexdigest()[:16]
        key = f"flux_api/{digest}.png"
        await self._storage.put_object(self._bucket, key, data, "image/png")
        return key

    async def health_check(self) -> None:
        # BFL has no documented lightweight status endpoint — a bare-root
        # probe at least confirms the host is reachable and, via any 401/403,
        # that the key is rejected. # verify against current provider docs.
        await self._client.ping("/")

    async def _poll(self, request_id: str) -> str:
        elapsed = 0.0
        while elapsed < _POLL_TIMEOUT_S:
            body = await self._client.get_json("/get_result", {"id": request_id})
            if body.get("status") == "Ready":
                url: str = body["result"]["sample"]
                return url
            if body.get("status") in ("Error", "Failed"):
                raise ProviderRequestError("flux_api", f"generation failed: {body}")
            await asyncio.sleep(_POLL_INTERVAL_S)
            elapsed += _POLL_INTERVAL_S
        raise ProviderRequestError("flux_api", f"timed out waiting for job {request_id}")
