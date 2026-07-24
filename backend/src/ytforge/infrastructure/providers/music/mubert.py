from __future__ import annotations

import hashlib

import httpx

from ytforge.application.dto.music import MusicAsset, MusicRequest
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_BASE_URL = "https://api-b2b.mubert.com/v2"


class MubertProvider:
    """Mubert generative music API — synchronous response (no polling).
    # verify against current provider docs; field names below are a
    # best-effort approximation. `download_link` is provider-hosted —
    # downloaded and re-uploaded into our object storage (ARCHITECTURE.md
    # §6.3) rather than returned as-is."""

    def __init__(self, api_key: str, storage: ObjectStorage, bucket: str, cost_per_generation_usd: float | None = None) -> None:
        self._client = ProviderHttpClient("mubert", _BASE_URL)
        self._api_key = api_key
        self._storage = storage
        self._bucket = bucket
        self._cost_per_generation = cost_per_generation_usd

    async def generate(self, req: MusicRequest) -> MusicAsset:
        async with record_provider_call("mubert", "music.generate") as metric:
            body = await self._client.post_json(
                "/TTMRun",
                {
                    "method": "TTMRun",
                    "params": {
                        "pat": self._api_key,
                        "text": req.prompt,
                        "duration": req.duration_seconds,
                        "mode": req.model,
                    },
                },
            )
            provider_url = body["data"]["tasks"][0]["download_link"]
            object_key = await self._download_and_store(provider_url)
            metric.cost_usd = self._cost_per_generation
            return MusicAsset(
                object_key=object_key,
                content_type="audio/mpeg",
                duration_seconds=req.duration_seconds,
                model=req.model,
                latency_ms=0,
                cost_usd=self._cost_per_generation,
            )

    async def _download_and_store(self, provider_url: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(provider_url, timeout=httpx.Timeout(connect=5.0, read=60.0, write=30.0, pool=5.0))
            response.raise_for_status()
            data = response.content
        digest = hashlib.sha256(data).hexdigest()[:16]
        key = f"mubert/{digest}.mp3"
        await self._storage.put_object(self._bucket, key, data, "audio/mpeg")
        return key
