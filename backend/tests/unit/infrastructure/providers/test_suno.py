from __future__ import annotations

import httpx
import pytest
import respx

from ytforge.application.dto.music import MusicRequest
from ytforge.infrastructure.providers.errors import ProviderRequestError
from ytforge.infrastructure.providers.music import suno as suno_module
from ytforge.infrastructure.providers.music.suno import SunoProvider
from ytforge.infrastructure.storage.fake import FakeObjectStorage


@pytest.fixture(autouse=True)
def _fast_poll(monkeypatch: pytest.MonkeyPatch) -> None:
    # Real adapter sleeps 3s between polls; tests exercise the polling
    # loop's branching logic, not real wall-clock timing.
    async def _no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(suno_module.asyncio, "sleep", _no_sleep)


@respx.mock
async def test_generate_returns_asset_once_clip_completes() -> None:
    respx.post("https://api.suno.ai/v1/generate").mock(return_value=httpx.Response(200, json={"id": "clip-1"}))
    respx.get("https://api.suno.ai/v1/clips/clip-1").mock(
        side_effect=[
            httpx.Response(200, json={"status": "processing"}),
            httpx.Response(200, json={"status": "complete", "audio_url": "https://cdn.suno.ai/clip-1.mp3"}),
        ]
    )
    respx.get("https://cdn.suno.ai/clip-1.mp3").mock(return_value=httpx.Response(200, content=b"suno-mp3-bytes"))
    storage = FakeObjectStorage()
    provider = SunoProvider(api_key="key-1", storage=storage, bucket="raw-assets", cost_per_generation_usd=0.25)

    asset = await provider.generate(MusicRequest(prompt="lofi beat", model="v3", duration_seconds=30.0))

    assert not asset.object_key.startswith("https://")
    assert await storage.get_object("raw-assets", asset.object_key) == b"suno-mp3-bytes"
    assert asset.cost_usd == 0.25
    assert asset.duration_seconds == 30.0


@respx.mock
async def test_generate_raises_on_clip_error_status() -> None:
    respx.post("https://api.suno.ai/v1/generate").mock(return_value=httpx.Response(200, json={"id": "clip-2"}))
    respx.get("https://api.suno.ai/v1/clips/clip-2").mock(return_value=httpx.Response(200, json={"status": "error"}))
    provider = SunoProvider(api_key="key-1", storage=FakeObjectStorage(), bucket="raw-assets")

    with pytest.raises(ProviderRequestError, match="generation failed"):
        await provider.generate(MusicRequest(prompt="lofi beat", model="v3", duration_seconds=30.0))


@respx.mock
async def test_generate_times_out_if_never_complete() -> None:
    respx.post("https://api.suno.ai/v1/generate").mock(return_value=httpx.Response(200, json={"id": "clip-3"}))
    respx.get("https://api.suno.ai/v1/clips/clip-3").mock(return_value=httpx.Response(200, json={"status": "processing"}))
    provider = SunoProvider(api_key="key-1", storage=FakeObjectStorage(), bucket="raw-assets")

    with pytest.raises(ProviderRequestError, match="timed out"):
        await provider.generate(MusicRequest(prompt="lofi beat", model="v3", duration_seconds=30.0))
