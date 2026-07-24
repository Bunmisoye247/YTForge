from __future__ import annotations

import base64

import httpx
import pytest
import respx

from ytforge.application.dto.tts import TTSRequest, VoiceCloneRequest
from ytforge.infrastructure.providers.errors import ProviderRateLimitError
from ytforge.infrastructure.providers.tts.elevenlabs import ElevenLabsProvider
from ytforge.infrastructure.storage.fake import FakeObjectStorage

_AUDIO_BYTES = b"fake-mp3-bytes"


def _alignment_for(text: str) -> dict[str, list]:
    # One char = 0.1s, so "hi there" is fully deterministic to assert on.
    starts = [i * 0.1 for i in range(len(text))]
    ends = [s + 0.1 for s in starts]
    return {"characters": list(text), "character_start_times_seconds": starts, "character_end_times_seconds": ends}


@respx.mock
async def test_synthesize_groups_characters_into_words_with_timestamps() -> None:
    text = "hi there"
    respx.post("https://api.elevenlabs.io/v1/text-to-speech/voice-1/with-timestamps").mock(
        return_value=httpx.Response(
            200,
            json={
                "audio_base64": base64.b64encode(_AUDIO_BYTES).decode(),
                "alignment": _alignment_for(text),
            },
        )
    )
    storage = FakeObjectStorage()
    provider = ElevenLabsProvider(api_key="key-1", storage=storage, bucket="raw-assets", cost_per_1k_chars_usd=1.0)

    asset = await provider.synthesize(TTSRequest(text=text, model="eleven_v2", voice_id="voice-1"))

    assert [w.word for w in asset.word_timestamps] == ["hi", "there"]
    assert asset.duration_seconds == pytest.approx(asset.word_timestamps[-1].end)
    assert asset.cost_usd == pytest.approx((len(text) / 1000) * 1.0)
    assert asset.content_type == "audio/mpeg"
    assert not asset.object_key.startswith("https://")
    assert await storage.get_object("raw-assets", asset.object_key) == _AUDIO_BYTES


@respx.mock
async def test_synthesize_sends_api_key_header() -> None:
    route = respx.post("https://api.elevenlabs.io/v1/text-to-speech/voice-1/with-timestamps").mock(
        return_value=httpx.Response(
            200, json={"audio_base64": base64.b64encode(_AUDIO_BYTES).decode(), "alignment": _alignment_for("hi")}
        )
    )
    provider = ElevenLabsProvider(api_key="secret-key", storage=FakeObjectStorage(), bucket="raw-assets")

    await provider.synthesize(TTSRequest(text="hi", model="eleven_v2", voice_id="voice-1"))

    assert route.calls.last.request.headers["xi-api-key"] == "secret-key"


@respx.mock
async def test_synthesize_raises_rate_limit_error_on_429() -> None:
    respx.post("https://api.elevenlabs.io/v1/text-to-speech/voice-1/with-timestamps").mock(
        return_value=httpx.Response(429, text="too many requests")
    )
    provider = ElevenLabsProvider(api_key="key-1", storage=FakeObjectStorage(), bucket="raw-assets")

    with pytest.raises(ProviderRateLimitError):
        await provider.synthesize(TTSRequest(text="hi", model="eleven_v2", voice_id="voice-1"))


@respx.mock
async def test_clone_voice_returns_provider_voice_id() -> None:
    respx.post("https://api.elevenlabs.io/v1/voices/add").mock(
        return_value=httpx.Response(200, json={"voice_id": "cloned-123"})
    )
    provider = ElevenLabsProvider(api_key="key-1", storage=FakeObjectStorage(), bucket="raw-assets")

    result = await provider.clone_voice(
        VoiceCloneRequest(name="My Voice", sample_object_keys=["a.wav"], consent_artifact_object_key="consent.pdf")
    )

    assert result.provider_voice_id == "cloned-123"
