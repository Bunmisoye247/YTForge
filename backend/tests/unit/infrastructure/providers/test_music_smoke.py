from __future__ import annotations

import httpx
import pytest
import respx

from ytforge.application.dto.music import MusicRequest
from ytforge.infrastructure.providers.music import udio as udio_module
from ytforge.infrastructure.providers.music.mubert import MubertProvider
from ytforge.infrastructure.providers.music.udio import UdioProvider
from ytforge.infrastructure.storage.fake import FakeObjectStorage


@pytest.fixture(autouse=True)
def _fast_poll(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(udio_module.asyncio, "sleep", _no_sleep)


def _request() -> MusicRequest:
    return MusicRequest(prompt="lofi beat", model="model-x", duration_seconds=30.0)


@respx.mock
async def test_udio_generate_smoke() -> None:
    respx.post("https://api.udio.com/v1/generations").mock(return_value=httpx.Response(200, json={"id": "gen-1"}))
    respx.get("https://api.udio.com/v1/generations/gen-1").mock(
        return_value=httpx.Response(200, json={"status": "completed", "audio_url": "https://cdn/x.mp3"})
    )
    respx.get("https://cdn/x.mp3").mock(return_value=httpx.Response(200, content=b"udio-mp3-bytes"))
    provider = UdioProvider(api_key="key-1", storage=FakeObjectStorage(), bucket="raw-assets", cost_per_generation_usd=0.5)

    asset = await provider.generate(_request())

    assert not asset.object_key.startswith("https://")
    assert asset.cost_usd == 0.5


@respx.mock
async def test_mubert_generate_smoke() -> None:
    respx.post("https://api-b2b.mubert.com/v2/TTMRun").mock(
        return_value=httpx.Response(
            200, json={"data": {"tasks": [{"download_link": "https://cdn/mubert.mp3"}]}}
        )
    )
    respx.get("https://cdn/mubert.mp3").mock(return_value=httpx.Response(200, content=b"mubert-mp3-bytes"))
    provider = MubertProvider(api_key="key-1", storage=FakeObjectStorage(), bucket="raw-assets", cost_per_generation_usd=0.1)

    asset = await provider.generate(_request())

    assert not asset.object_key.startswith("https://")
    assert asset.cost_usd == 0.1
