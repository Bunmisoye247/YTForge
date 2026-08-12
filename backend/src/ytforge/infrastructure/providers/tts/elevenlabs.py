from __future__ import annotations

import base64
import hashlib
from typing import Any

from ytforge.application.dto.tts import (
    AudioAsset,
    ClonedVoice,
    TTSRequest,
    VoiceCloneRequest,
    WordTimestamp,
)
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_BASE_URL = "https://api.elevenlabs.io/v1"


def _group_into_words(alignment: dict[str, list[Any]]) -> list[WordTimestamp]:
    """ElevenLabs' with-timestamps endpoint returns character-level
    alignment; group it into word-level timestamps (what AudioAsset
    carries, matching the seed data's `word_timestamps` shape)."""
    chars = alignment["characters"]
    starts = alignment["character_start_times_seconds"]
    ends = alignment["character_end_times_seconds"]

    words: list[WordTimestamp] = []
    word_chars: list[str] = []
    word_start: float | None = None
    for char, start, end in zip(chars, starts, ends, strict=True):
        if char.isspace():
            if word_chars:
                words.append(WordTimestamp(word="".join(word_chars), start=word_start or 0.0, end=end))
                word_chars = []
                word_start = None
            continue
        if word_start is None:
            word_start = start
        word_chars.append(char)
    if word_chars:
        words.append(WordTimestamp(word="".join(word_chars), start=word_start or 0.0, end=ends[-1]))
    return words


class ElevenLabsProvider:
    """ElevenLabs Text-to-Speech + voice cloning API.
    https://elevenlabs.io/docs/api-reference"""

    def __init__(self, api_key: str, storage: ObjectStorage, bucket: str, cost_per_1k_chars_usd: float | None = None) -> None:
        self._client = ProviderHttpClient("elevenlabs", _BASE_URL, {"xi-api-key": api_key})
        self._storage = storage
        self._bucket = bucket
        self._cost_per_1k_chars = cost_per_1k_chars_usd

    async def synthesize(self, req: TTSRequest) -> AudioAsset:
        async with record_provider_call("elevenlabs", "tts.synthesize") as metric:
            body = await self._client.post_json(
                f"/text-to-speech/{req.voice_id}/with-timestamps",
                {"text": req.text, "model_id": req.model},
            )
            audio_bytes = base64.b64decode(body["audio_base64"])
            words = _group_into_words(body["alignment"])
            duration = words[-1].end if words else 0.0
            cost = self._estimate_cost(len(req.text))
            metric.cost_usd = cost
            digest = hashlib.sha256(audio_bytes).hexdigest()[:16]
            key = f"elevenlabs/{digest}.mp3"
            await self._storage.put_object(self._bucket, key, audio_bytes, "audio/mpeg")
            return AudioAsset(
                object_key=key,
                content_type="audio/mpeg",
                duration_seconds=duration,
                model=req.model,
                latency_ms=0,
                word_timestamps=words,
                cost_usd=cost,
            )

    async def clone_voice(self, req: VoiceCloneRequest) -> ClonedVoice:
        """Approval-gated by the caller (see dto.tts.VoiceCloneRequest) —
        this adapter just performs the call once a VOICE_CLONING approval
        has already been granted."""
        async with record_provider_call("elevenlabs", "tts.clone_voice"):
            body = await self._client.post_json(
                "/voices/add",
                {"name": req.name, "files": req.sample_object_keys},
            )
            return ClonedVoice(provider_voice_id=body["voice_id"], model="eleven_multilingual_v2")

    async def health_check(self) -> None:
        await self._client.ping("/user")

    def _estimate_cost(self, char_count: int) -> float | None:
        if self._cost_per_1k_chars is None:
            return None
        return round((char_count / 1000) * self._cost_per_1k_chars, 6)
