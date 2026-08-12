from __future__ import annotations

import json

import httpx
import pytest
import respx

from ytforge.application.dto.tts import TTSRequest
from ytforge.infrastructure.providers.errors import ProviderRequestError
from ytforge.infrastructure.providers.tts.kokoro import KokoroProvider
from ytforge.infrastructure.storage.fake import FakeObjectStorage


def _request(**overrides: object) -> TTSRequest:
    defaults: dict[str, object] = {"text": "hello world", "model": "kokoro-v1", "voice_id": "af_heart"}
    defaults.update(overrides)
    return TTSRequest(**defaults)  # type: ignore[arg-type]


@respx.mock
async def test_synthesize_posts_elevenlabs_shaped_request_to_voice_id_path() -> None:
    route = respx.post("http://localhost:8880/v1/text-to-speech/af_heart").mock(
        return_value=httpx.Response(200, content=b"mp3-bytes")
    )
    provider = KokoroProvider(base_url="http://localhost:8880", storage=FakeObjectStorage(), bucket="raw-assets")

    await provider.synthesize(_request())

    request = route.calls.last.request
    assert request.url.params["output_format"] == "mp3_44100_128"
    body = json.loads(request.content)
    assert body["text"] == "hello world"
    assert body["voice_settings"] == {"speed": 1.0}


@respx.mock
async def test_synthesize_uses_the_requested_voice_id() -> None:
    route = respx.post("http://localhost:8880/v1/text-to-speech/bm_george").mock(
        return_value=httpx.Response(200, content=b"mp3-bytes")
    )
    provider = KokoroProvider(base_url="http://localhost:8880", storage=FakeObjectStorage(), bucket="raw-assets")

    await provider.synthesize(_request(voice_id="bm_george"))

    assert route.called


@respx.mock
async def test_synthesize_stores_returned_bytes_and_reports_zero_cost() -> None:
    respx.post("http://localhost:8880/v1/text-to-speech/af_heart").mock(
        return_value=httpx.Response(200, content=b"mp3-bytes")
    )
    storage = FakeObjectStorage()
    provider = KokoroProvider(base_url="http://localhost:8880", storage=storage, bucket="raw-assets")

    asset = await provider.synthesize(_request())

    assert asset.cost_usd == 0.0
    assert asset.content_type == "audio/mpeg"
    assert await storage.get_object("raw-assets", asset.object_key) == b"mp3-bytes"


@respx.mock
async def test_synthesize_raises_on_error_response() -> None:
    respx.post("http://localhost:8880/v1/text-to-speech/af_heart").mock(
        return_value=httpx.Response(400, json={"detail": "Unknown voice"})
    )
    provider = KokoroProvider(base_url="http://localhost:8880", storage=FakeObjectStorage(), bucket="raw-assets")

    with pytest.raises(ProviderRequestError):
        await provider.synthesize(_request())


async def test_clone_voice_is_not_supported() -> None:
    from ytforge.application.dto.tts import VoiceCloneRequest

    provider = KokoroProvider(base_url="http://localhost:8880", storage=FakeObjectStorage(), bucket="raw-assets")

    with pytest.raises(NotImplementedError):
        await provider.clone_voice(
            VoiceCloneRequest(name="x", sample_object_keys=[], consent_artifact_object_key="c")
        )


@respx.mock
async def test_health_check_succeeds_on_200() -> None:
    respx.get("http://localhost:8880/health").mock(
        return_value=httpx.Response(200, json={"status": "ok", "engine": "kokoro"})
    )
    provider = KokoroProvider(base_url="http://localhost:8880", storage=FakeObjectStorage(), bucket="raw-assets")

    await provider.health_check()


@respx.mock
async def test_health_check_raises_when_service_is_down() -> None:
    respx.get("http://localhost:8880/health").mock(side_effect=httpx.ConnectError("connection refused"))
    provider = KokoroProvider(base_url="http://localhost:8880", storage=FakeObjectStorage(), bucket="raw-assets")

    with pytest.raises(ProviderRequestError):
        await provider.health_check()
