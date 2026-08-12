from __future__ import annotations

import httpx
import pytest
import respx

from ytforge.application.dto.image import ImageRequest
from ytforge.infrastructure.providers.errors import ProviderRequestError
from ytforge.infrastructure.providers.image.pollinations import PollinationsProvider
from ytforge.infrastructure.storage.fake import FakeObjectStorage


@respx.mock
async def test_generate_returns_one_asset_per_image_with_zero_cost() -> None:
    respx.get(url__startswith="https://image.pollinations.ai/prompt/").mock(
        return_value=httpx.Response(200, content=b"jpeg-bytes", headers={"content-type": "image/jpeg"})
    )
    storage = FakeObjectStorage()
    provider = PollinationsProvider(base_url="https://image.pollinations.ai", storage=storage, bucket="raw-assets")

    assets = await provider.generate(ImageRequest(prompt="a red bicycle", model="flux", count=2))

    assert len(assets) == 2
    assert all(a.cost_usd == 0.0 for a in assets)
    assert all(a.content_type == "image/jpeg" for a in assets)
    assert await storage.get_object("raw-assets", assets[0].object_key) == b"jpeg-bytes"


@respx.mock
async def test_generate_url_encodes_prompt_and_sends_dimensions() -> None:
    route = respx.get(url__startswith="https://image.pollinations.ai/prompt/").mock(
        return_value=httpx.Response(200, content=b"x")
    )
    provider = PollinationsProvider(
        base_url="https://image.pollinations.ai", storage=FakeObjectStorage(), bucket="raw-assets"
    )

    await provider.generate(ImageRequest(prompt="a red bicycle & sunset", model="flux", width=768, height=512))

    request = route.calls.last.request
    assert "a%20red%20bicycle" in str(request.url) or "a+red+bicycle" in str(request.url)
    assert request.url.params["width"] == "768"
    assert request.url.params["height"] == "512"
    assert request.url.params["model"] == "flux"


@respx.mock
async def test_generate_omits_token_param_when_no_api_key_configured() -> None:
    route = respx.get(url__startswith="https://image.pollinations.ai/prompt/").mock(
        return_value=httpx.Response(200, content=b"x")
    )
    provider = PollinationsProvider(
        base_url="https://image.pollinations.ai", storage=FakeObjectStorage(), bucket="raw-assets"
    )

    await provider.generate(ImageRequest(prompt="a cat", model="flux"))

    assert "token" not in route.calls.last.request.url.params


@respx.mock
async def test_generate_includes_token_param_when_api_key_configured() -> None:
    route = respx.get(url__startswith="https://image.pollinations.ai/prompt/").mock(
        return_value=httpx.Response(200, content=b"x")
    )
    provider = PollinationsProvider(
        base_url="https://image.pollinations.ai",
        storage=FakeObjectStorage(),
        bucket="raw-assets",
        api_key="registered-token",
    )

    await provider.generate(ImageRequest(prompt="a cat", model="flux"))

    assert route.calls.last.request.url.params["token"] == "registered-token"


@respx.mock
async def test_generate_raises_on_error_response() -> None:
    respx.get(url__startswith="https://image.pollinations.ai/prompt/").mock(return_value=httpx.Response(500))
    provider = PollinationsProvider(
        base_url="https://image.pollinations.ai", storage=FakeObjectStorage(), bucket="raw-assets"
    )

    with pytest.raises(ProviderRequestError):
        await provider.generate(ImageRequest(prompt="a cat", model="flux"))


@respx.mock
async def test_generate_folds_negative_prompt_into_prompt_text() -> None:
    """Pollinations has no negative_prompt parameter — it must be folded
    into the prompt text itself."""
    route = respx.get(url__startswith="https://image.pollinations.ai/prompt/").mock(
        return_value=httpx.Response(200, content=b"x")
    )
    provider = PollinationsProvider(
        base_url="https://image.pollinations.ai", storage=FakeObjectStorage(), bucket="raw-assets"
    )

    await provider.generate(ImageRequest(prompt="a cat", model="flux", negative_prompt="blurry"))

    request = route.calls.last.request
    assert "negative_prompt" not in request.url.params
    assert "Avoid" in str(request.url)


@respx.mock
async def test_health_check_succeeds_on_200() -> None:
    respx.get("https://image.pollinations.ai/prompt/test").mock(return_value=httpx.Response(200, content=b"x"))
    provider = PollinationsProvider(
        base_url="https://image.pollinations.ai", storage=FakeObjectStorage(), bucket="raw-assets"
    )

    await provider.health_check()


@respx.mock
async def test_health_check_raises_on_error() -> None:
    respx.get("https://image.pollinations.ai/prompt/test").mock(return_value=httpx.Response(503))
    provider = PollinationsProvider(
        base_url="https://image.pollinations.ai", storage=FakeObjectStorage(), bucket="raw-assets"
    )

    with pytest.raises(ProviderRequestError):
        await provider.health_check()
