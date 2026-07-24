from __future__ import annotations

import asyncio
import hashlib

import httpx

from ytforge.application.dto.music import MusicAsset, MusicRequest
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.errors import ProviderRequestError
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_BASE_URL = "https://api.suno.ai/v1"
_POLL_INTERVAL_S = 3.0
_POLL_TIMEOUT_S = 180.0


class SunoProvider:
    """Suno AI music generation API — async submit-then-poll job pattern.
    # verify against current provider docs; field names below are a
    # best-effort approximation. The completed clip's `audio_url` is
    # provider-hosted — downloaded and re-uploaded into our object storage
    # (ARCHITECTURE.md §6.3) rather than returned as-is."""

    def __init__(self, api_key: str, storage: ObjectStorage, bucket: str, cost_per_generation_usd: float | None = None) -> None:
        self._client = ProviderHttpClient("suno", _BASE_URL, {"Authorization": f"Bearer {api_key}"})
        self._storage = storage
        self._bucket = bucket
        self._cost_per_generation = cost_per_generation_usd

    async def generate(self, req: MusicRequest) -> MusicAsset:
        async with record_provider_call("suno", "music.generate") as metric:
            submit = await self._client.post_json(
                "/generate",
                {"prompt": req.prompt, "model": req.model, "duration": req.duration_seconds},
            )
            clip_id = submit["id"]
            provider_url = await self._poll(clip_id)
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

    async def _poll(self, clip_id: str) -> str:
        elapsed = 0.0
        while elapsed < _POLL_TIMEOUT_S:
            body = await self._client.get_json(f"/clips/{clip_id}")
            if body["status"] == "complete":
                url: str = body["audio_url"]
                return url
            if body["status"] == "error":
                raise ProviderRequestError("suno", f"generation failed: {body}")
            await asyncio.sleep(_POLL_INTERVAL_S)
            elapsed += _POLL_INTERVAL_S
        raise ProviderRequestError("suno", f"timed out waiting for clip {clip_id}")

    async def _download_and_store(self, provider_url: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(provider_url, timeout=httpx.Timeout(connect=5.0, read=60.0, write=30.0, pool=5.0))
            response.raise_for_status()
            data = response.content
        digest = hashlib.sha256(data).hexdigest()[:16]
        key = f"suno/{digest}.mp3"
        await self._storage.put_object(self._bucket, key, data, "audio/mpeg")
        return key
