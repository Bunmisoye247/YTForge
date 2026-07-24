from __future__ import annotations

import hashlib

import httpx

from ytforge.application.dto.tts import AudioAsset, ClonedVoice, TTSRequest, VoiceCloneRequest
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.errors import ProviderRequestError
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call


class KokoroProvider:
    """Local Kokoro TTS server (open-weight, commonly served via an
    OpenAI-compatible `/v1/audio/speech` wrapper, e.g. kokoro-FastAPI).
    Free/local — cost is always 0.
    # verify request/response shape against your actual server wrapper."""

    def __init__(self, base_url: str, storage: ObjectStorage, bucket: str) -> None:
        self._base_url = base_url
        self._storage = storage
        self._bucket = bucket

    async def synthesize(self, req: TTSRequest) -> AudioAsset:
        async with record_provider_call("kokoro", "tts.synthesize") as metric:
            async with httpx.AsyncClient(base_url=self._base_url) as client:
                response = await client.post(
                    "/v1/audio/speech",
                    json={"model": req.model, "voice": req.voice_id, "input": req.text},
                )
            if response.status_code >= 400:
                raise ProviderRequestError("kokoro", f"HTTP {response.status_code}: {response.text[:200]}")
            digest = hashlib.sha256(response.content).hexdigest()[:16]
            metric.cost_usd = 0.0
            key = f"kokoro/{digest}.mp3"
            await self._storage.put_object(self._bucket, key, response.content, "audio/mpeg")
            return AudioAsset(
                object_key=key,
                content_type="audio/mpeg",
                duration_seconds=0.0,
                model=req.model,
                latency_ms=0,
                cost_usd=0.0,
            )

    async def clone_voice(self, req: VoiceCloneRequest) -> ClonedVoice:
        raise NotImplementedError("Kokoro does not support voice cloning")
