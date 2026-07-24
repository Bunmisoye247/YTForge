from __future__ import annotations

import base64

import httpx
import pytest
import respx

from ytforge.application.dto.image import ImageRequest
from ytforge.infrastructure.providers.image import comfyui as comfyui_module
from ytforge.infrastructure.providers.image import flux_api as flux_api_module
from ytforge.infrastructure.providers.image.comfyui import ComfyUIProvider
from ytforge.infrastructure.providers.image.flux_api import FluxApiProvider
from ytforge.infrastructure.providers.image.sdxl_diffusers import SdxlDiffusersProvider
from ytforge.infrastructure.storage.fake import FakeObjectStorage


@pytest.fixture(autouse=True)
def _fast_poll(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(flux_api_module.asyncio, "sleep", _no_sleep)
    monkeypatch.setattr(comfyui_module.asyncio, "sleep", _no_sleep)


def _request(**overrides: object) -> ImageRequest:
    defaults: dict[str, object] = {"prompt": "a red bicycle", "model": "flux-pro", "count": 1}
    defaults.update(overrides)
    return ImageRequest(**defaults)  # type: ignore[arg-type]


@respx.mock
async def test_flux_api_generate_smoke() -> None:
    respx.post("https://api.bfl.ml/v1/flux-pro").mock(return_value=httpx.Response(200, json={"id": "job-1"}))
    respx.get("https://api.bfl.ml/v1/get_result").mock(
        return_value=httpx.Response(200, json={"status": "Ready", "result": {"sample": "https://cdn/x.png"}})
    )
    respx.get("https://cdn/x.png").mock(return_value=httpx.Response(200, content=b"flux-png-bytes"))
    provider = FluxApiProvider(api_key="key-1", storage=FakeObjectStorage(), bucket="raw-assets", cost_per_image_usd=0.05)

    assets = await provider.generate(_request())

    assert len(assets) == 1
    assert not assets[0].object_key.startswith("https://")


@respx.mock
async def test_sdxl_diffusers_generate_smoke() -> None:
    respx.post("http://localhost:8000/generate").mock(
        return_value=httpx.Response(200, json={"images": [base64.b64encode(b"png-bytes").decode()]})
    )
    provider = SdxlDiffusersProvider(base_url="http://localhost:8000", storage=FakeObjectStorage(), bucket="raw-assets")

    assets = await provider.generate(_request(model="sdxl-base"))

    assert len(assets) == 1
    assert assets[0].cost_usd == 0.0


@respx.mock
async def test_comfyui_generate_smoke() -> None:
    respx.post("http://localhost:8188/prompt").mock(return_value=httpx.Response(200, json={"prompt_id": "p1"}))
    respx.get("http://localhost:8188/history/p1").mock(
        return_value=httpx.Response(
            200,
            json={"p1": {"outputs": {"9": {"images": [{"filename": "ComfyUI_00001.png"}]}}}},
        )
    )
    respx.get("http://localhost:8188/view").mock(return_value=httpx.Response(200, content=b"comfy-png-bytes"))
    provider = ComfyUIProvider(base_url="http://localhost:8188", storage=FakeObjectStorage(), bucket="raw-assets")

    assets = await provider.generate(_request(model="sd_xl_base"))

    assert len(assets) == 1
    assert not assets[0].object_key.startswith("pending-upload/")
