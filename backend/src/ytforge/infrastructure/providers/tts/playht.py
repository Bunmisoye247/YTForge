from __future__ import annotations

import hashlib

import httpx

from ytforge.application.dto.tts import AudioAsset, ClonedVoice, TTSRequest, VoiceCloneRequest
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_BASE_URL = "https://api.play.ht/api/v2"


class PlayHTProvider:
    """PlayHT Text-to-Speech API.
    https://docs.play.ht/reference # verify against current provider docs.
    The response is a provider-hosted URL, not bytes — downloaded and
    re-uploaded into our object storage (ARCHITECTURE.md §6.3)."""

    def __init__(
        self, api_key: str, user_id: str, storage: ObjectStorage, bucket: str, cost_per_1k_chars_usd: float | None = None
    ) -> None:
        self._client = ProviderHttpClient(
            "playht", _BASE_URL, {"Authorization": f"Bearer {api_key}", "X-User-ID": user_id}
        )
        self._storage = storage
        self._bucket = bucket
        self._cost_per_1k_chars = cost_per_1k_chars_usd

    async def synthesize(self, req: TTSRequest) -> AudioAsset:
        async with record_provider_call("playht", "tts.synthesize") as metric:
            body = await self._client.post_json(
                "/tts", {"text": req.text, "voice": req.voice_id, "voice_engine": req.model}
            )
            cost = self._estimate_cost(len(req.text))
            metric.cost_usd = cost
            object_key = await self._download_and_store(body["url"])
            return AudioAsset(
                object_key=object_key,
                content_type="audio/mpeg",
                duration_seconds=body.get("duration", 0.0),
                model=req.model,
                latency_ms=0,
                cost_usd=cost,
            )

    async def _download_and_store(self, provider_url: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(provider_url, timeout=httpx.Timeout(connect=5.0, read=60.0, write=30.0, pool=5.0))
            response.raise_for_status()
            data = response.content
        digest = hashlib.sha256(data).hexdigest()[:16]
        key = f"playht/{digest}.mp3"
        await self._storage.put_object(self._bucket, key, data, "audio/mpeg")
        return key

    async def clone_voice(self, req: VoiceCloneRequest) -> ClonedVoice:
        async with record_provider_call("playht", "tts.clone_voice"):
            body = await self._client.post_json(
                "/cloned-voices/instant",
                {"voice_name": req.name, "sample_file_url": req.sample_object_keys[0]},
            )
            return ClonedVoice(provider_voice_id=body["id"], model="PlayHT2.0")

    async def health_check(self) -> None:
        await self._client.ping("/voices")

    def _estimate_cost(self, char_count: int) -> float | None:
        if self._cost_per_1k_chars is None:
            return None
        return round((char_count / 1000) * self._cost_per_1k_chars, 6)
