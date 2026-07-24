from __future__ import annotations

import base64

import httpx
import respx

from ytforge.application.dto.image import ImageRequest
from ytforge.infrastructure.providers.image.a1111 import A1111Provider
from ytforge.infrastructure.storage.fake import FakeObjectStorage


@respx.mock
async def test_generate_returns_one_asset_per_image_with_zero_cost() -> None:
    respx.post("http://localhost:7860/sdapi/v1/txt2img").mock(
        return_value=httpx.Response(
            200,
            json={"images": [base64.b64encode(b"png-bytes-1").decode(), base64.b64encode(b"png-bytes-2").decode()]},
        )
    )
    storage = FakeObjectStorage()
    provider = A1111Provider(base_url="http://localhost:7860", storage=storage, bucket="raw-assets")

    assets = await provider.generate(
        ImageRequest(prompt="a red bicycle", model="sd_xl_base", count=2, width=512, height=512)
    )

    assert len(assets) == 2
    assert all(a.cost_usd == 0.0 for a in assets)
    assert all(a.content_type == "image/png" for a in assets)
    assert assets[0].object_key != assets[1].object_key
    assert await storage.get_object("raw-assets", assets[0].object_key) == b"png-bytes-1"
    assert await storage.get_object("raw-assets", assets[1].object_key) == b"png-bytes-2"


@respx.mock
async def test_generate_sends_prompt_and_dimensions_in_body() -> None:
    route = respx.post("http://localhost:7860/sdapi/v1/txt2img").mock(
        return_value=httpx.Response(200, json={"images": [base64.b64encode(b"x").decode()]})
    )
    provider = A1111Provider(base_url="http://localhost:7860", storage=FakeObjectStorage(), bucket="raw-assets")

    await provider.generate(
        ImageRequest(prompt="a red bicycle", model="sd_xl_base", negative_prompt="blurry", width=768, height=512)
    )

    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body["prompt"] == "a red bicycle"
    assert body["negative_prompt"] == "blurry"
    assert body["width"] == 768
    assert body["height"] == 512
    assert body["override_settings"]["sd_model_checkpoint"] == "sd_xl_base"
