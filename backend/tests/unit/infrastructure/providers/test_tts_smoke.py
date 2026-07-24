from __future__ import annotations

import httpx
import respx

from ytforge.application.dto.tts import TTSRequest
from ytforge.infrastructure.providers.tts.azure_tts import AzureTtsProvider
from ytforge.infrastructure.providers.tts.kokoro import KokoroProvider
from ytforge.infrastructure.providers.tts.piper import PiperProvider
from ytforge.infrastructure.providers.tts.playht import PlayHTProvider
from ytforge.infrastructure.storage.fake import FakeObjectStorage


def _request(**overrides: object) -> TTSRequest:
    defaults: dict[str, object] = {"text": "hello world", "model": "model-x", "voice_id": "voice-1"}
    defaults.update(overrides)
    return TTSRequest(**defaults)  # type: ignore[arg-type]


@respx.mock
async def test_playht_synthesize_smoke() -> None:
    respx.post("https://api.play.ht/api/v2/tts").mock(
        return_value=httpx.Response(200, json={"url": "https://cdn/audio.mp3", "duration": 3.5})
    )
    respx.get("https://cdn/audio.mp3").mock(return_value=httpx.Response(200, content=b"playht-mp3-bytes"))
    provider = PlayHTProvider(
        api_key="key-1", user_id="user-1", storage=FakeObjectStorage(), bucket="raw-assets", cost_per_1k_chars_usd=1.0
    )

    asset = await provider.synthesize(_request())

    assert not asset.object_key.startswith("https://")
    assert asset.duration_seconds == 3.5


@respx.mock
async def test_playht_clone_voice_smoke() -> None:
    respx.post("https://api.play.ht/api/v2/cloned-voices/instant").mock(
        return_value=httpx.Response(200, json={"id": "cloned-1"})
    )
    provider = PlayHTProvider(api_key="key-1", user_id="user-1", storage=FakeObjectStorage(), bucket="raw-assets")

    from ytforge.application.dto.tts import VoiceCloneRequest

    result = await provider.clone_voice(
        VoiceCloneRequest(name="My Voice", sample_object_keys=["https://cdn/sample.wav"], consent_artifact_object_key="c.pdf")
    )

    assert result.provider_voice_id == "cloned-1"


@respx.mock
async def test_azure_tts_synthesize_smoke() -> None:
    respx.post("https://eastus.tts.speech.microsoft.com/cognitiveservices/v1").mock(
        return_value=httpx.Response(200, content=b"fake-mp3-bytes", headers={"content-type": "audio/mpeg"})
    )
    provider = AzureTtsProvider(
        api_key="key-1", region="eastus", storage=FakeObjectStorage(), bucket="raw-assets", cost_per_1k_chars_usd=1.0
    )

    asset = await provider.synthesize(_request())

    assert asset.content_type == "audio/mpeg"
    assert asset.object_key.startswith("azure_tts/")


@respx.mock
async def test_kokoro_synthesize_smoke() -> None:
    respx.post("http://localhost:8880/v1/audio/speech").mock(
        return_value=httpx.Response(200, content=b"fake-audio-bytes")
    )
    provider = KokoroProvider(base_url="http://localhost:8880", storage=FakeObjectStorage(), bucket="raw-assets")

    asset = await provider.synthesize(_request())

    assert asset.cost_usd == 0.0
    assert asset.object_key.startswith("kokoro/")


@respx.mock
async def test_piper_synthesize_smoke() -> None:
    respx.post("http://localhost:5000/synthesize").mock(
        return_value=httpx.Response(200, content=b"fake-wav-bytes")
    )
    provider = PiperProvider(base_url="http://localhost:5000", storage=FakeObjectStorage(), bucket="raw-assets")

    asset = await provider.synthesize(_request())

    assert asset.cost_usd == 0.0
    assert asset.content_type == "audio/wav"
