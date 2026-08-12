from __future__ import annotations

import hashlib

import httpx

from ytforge.application.dto.tts import AudioAsset, ClonedVoice, TTSRequest, VoiceCloneRequest
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.errors import ProviderAuthError, ProviderRequestError
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_HEALTH_TIMEOUT = httpx.Timeout(connect=3.0, read=5.0, write=3.0, pool=3.0)


class AzureTtsProvider:
    """Azure Cognitive Services Speech (TTS REST endpoint, SSML in / audio
    bytes out). https://learn.microsoft.com/azure/ai-services/speech-service/
    Word-level timestamps need the streaming Speech SDK, not the plain REST
    endpoint used here — `AudioAsset.word_timestamps` is empty for this
    provider; use elevenlabs/playht when word-level alignment matters."""

    def __init__(
        self, api_key: str, region: str, storage: ObjectStorage, bucket: str, cost_per_1k_chars_usd: float | None = None
    ) -> None:
        self._api_key = api_key
        self._base_url = f"https://{region}.tts.speech.microsoft.com"
        self._storage = storage
        self._bucket = bucket
        self._cost_per_1k_chars = cost_per_1k_chars_usd

    async def synthesize(self, req: TTSRequest) -> AudioAsset:
        async with record_provider_call("azure_tts", "tts.synthesize") as metric:
            ssml = (
                '<speak version="1.0" xml:lang="en-US">'
                f'<voice name="{req.voice_id}">{req.text}</voice></speak>'
            )
            async with httpx.AsyncClient(base_url=self._base_url) as client:
                response = await client.post(
                    "/cognitiveservices/v1",
                    content=ssml.encode("utf-8"),
                    headers={
                        "Ocp-Apim-Subscription-Key": self._api_key,
                        "Content-Type": "application/ssml+xml",
                        "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
                    },
                )
            if response.status_code >= 400:
                raise ProviderRequestError(
                    "azure_tts", f"HTTP {response.status_code}: {response.text[:200]}"
                )
            digest = hashlib.sha256(response.content).hexdigest()[:16]
            cost = self._estimate_cost(len(req.text))
            metric.cost_usd = cost
            key = f"azure_tts/{digest}.mp3"
            await self._storage.put_object(self._bucket, key, response.content, "audio/mpeg")
            return AudioAsset(
                object_key=key,
                content_type="audio/mpeg",
                duration_seconds=0.0,
                model=req.model,
                latency_ms=0,
                cost_usd=cost,
            )

    async def clone_voice(self, req: VoiceCloneRequest) -> ClonedVoice:
        raise NotImplementedError(
            "Azure custom neural voice cloning requires the long-running "
            "Custom Voice training pipeline, not a simple REST call — not "
            "implemented in this pass."
        )

    async def health_check(self) -> None:
        # Documented voices-list endpoint — cheap, requires the same
        # subscription key as synthesis.
        try:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=_HEALTH_TIMEOUT) as client:
                response = await client.get(
                    "/cognitiveservices/voices/list",
                    headers={"Ocp-Apim-Subscription-Key": self._api_key},
                )
        except httpx.HTTPError as exc:
            raise ProviderRequestError("azure_tts", f"health check failed: {exc}") from exc
        if response.status_code in (401, 403):
            raise ProviderAuthError("azure_tts", f"HTTP {response.status_code}: {response.text[:200]}")
        if response.status_code >= 400:
            raise ProviderRequestError("azure_tts", f"HTTP {response.status_code}: {response.text[:200]}")

    def _estimate_cost(self, char_count: int) -> float | None:
        if self._cost_per_1k_chars is None:
            return None
        return round((char_count / 1000) * self._cost_per_1k_chars, 6)
