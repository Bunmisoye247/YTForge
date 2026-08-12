from __future__ import annotations

import hashlib

import httpx

from ytforge.application.dto.tts import AudioAsset, ClonedVoice, TTSRequest, VoiceCloneRequest
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.errors import ProviderRequestError
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_HEALTH_TIMEOUT = httpx.Timeout(connect=3.0, read=5.0, write=3.0, pool=3.0)


class PiperProvider:
    """Local Piper TTS server (a small HTTP wrapper around the `piper`
    binary — e.g. the `piper --output_raw` + wyoming-piper HTTP bridge).
    Free/local — cost is always 0.
    # verify request/response shape against your actual server wrapper."""

    def __init__(self, base_url: str, storage: ObjectStorage, bucket: str) -> None:
        self._base_url = base_url
        self._storage = storage
        self._bucket = bucket

    async def synthesize(self, req: TTSRequest) -> AudioAsset:
        async with record_provider_call("piper", "tts.synthesize") as metric:
            async with httpx.AsyncClient(base_url=self._base_url) as client:
                response = await client.post(
                    "/synthesize", json={"text": req.text, "voice": req.voice_id}
                )
            if response.status_code >= 400:
                raise ProviderRequestError("piper", f"HTTP {response.status_code}: {response.text[:200]}")
            digest = hashlib.sha256(response.content).hexdigest()[:16]
            metric.cost_usd = 0.0
            key = f"piper/{digest}.wav"
            await self._storage.put_object(self._bucket, key, response.content, "audio/wav")
            return AudioAsset(
                object_key=key,
                content_type="audio/wav",
                duration_seconds=0.0,
                model=req.model,
                latency_ms=0,
                cost_usd=0.0,
            )

    async def clone_voice(self, req: VoiceCloneRequest) -> ClonedVoice:
        raise NotImplementedError("Piper does not support voice cloning")

    async def health_check(self) -> None:
        # No documented status endpoint for the wyoming-piper HTTP bridge —
        # bare-root probe. # verify against your actual server wrapper.
        try:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=_HEALTH_TIMEOUT) as client:
                response = await client.get("/")
        except httpx.HTTPError as exc:
            raise ProviderRequestError("piper", f"health check failed: {exc}") from exc
        if response.status_code >= 400:
            raise ProviderRequestError("piper", f"HTTP {response.status_code}: {response.text[:200]}")
