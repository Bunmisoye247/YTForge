from __future__ import annotations

import hashlib

from ytforge.application.dto.tts import AudioAsset, ClonedVoice, TTSRequest, VoiceCloneRequest
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_OUTPUT_FORMAT = "mp3_44100_128"


class KokoroProvider:
    """Local Kokoro TTS server — CPU-only, free, and deliberately served
    behind an ElevenLabs-shaped API (`POST /v1/text-to-speech/{voice_id}`,
    `GET /health`) so switching between the two is a base-url change, not
    a request-shape rewrite. `voice_id` is one of Kokoro's own voice ids
    (e.g. "af_heart"), not an ElevenLabs voice id — the shape is
    compatible, the catalog isn't."""

    def __init__(self, base_url: str, storage: ObjectStorage, bucket: str) -> None:
        self._client = ProviderHttpClient("kokoro", base_url)
        self._storage = storage
        self._bucket = bucket

    async def synthesize(self, req: TTSRequest) -> AudioAsset:
        async with record_provider_call("kokoro", "tts.synthesize") as metric:
            data = await self._client.post_bytes(
                f"/v1/text-to-speech/{req.voice_id}",
                {"text": req.text, "model_id": req.model, "voice_settings": {"speed": 1.0}},
                params={"output_format": _OUTPUT_FORMAT},
            )
            digest = hashlib.sha256(data).hexdigest()[:16]
            metric.cost_usd = 0.0
            key = f"kokoro/{digest}.mp3"
            await self._storage.put_object(self._bucket, key, data, "audio/mpeg")
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

    async def health_check(self) -> None:
        await self._client.ping("/health")
