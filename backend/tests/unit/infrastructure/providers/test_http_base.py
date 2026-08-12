from __future__ import annotations

import httpx
import pytest
import respx

from ytforge.infrastructure.providers.errors import ProviderRequestError
from ytforge.infrastructure.providers.http_base import ProviderHttpClient


@respx.mock
async def test_post_json_wraps_connection_error_as_provider_error() -> None:
    respx.post("https://example.test/api/chat").mock(side_effect=httpx.ConnectError("connection refused"))
    client = ProviderHttpClient("ollama", "https://example.test")

    with pytest.raises(ProviderRequestError):
        await client.post_json("/api/chat", {"model": "x"})


@respx.mock
async def test_get_json_wraps_connection_error_as_provider_error() -> None:
    respx.get("https://example.test/status").mock(side_effect=httpx.ConnectTimeout("timed out"))
    client = ProviderHttpClient("ollama", "https://example.test")

    with pytest.raises(ProviderRequestError):
        await client.get_json("/status")


@respx.mock
async def test_get_bytes_returns_raw_body() -> None:
    respx.get("https://example.test/image").mock(return_value=httpx.Response(200, content=b"raw-bytes"))
    client = ProviderHttpClient("pollinations", "https://example.test")

    result = await client.get_bytes("/image")

    assert result == b"raw-bytes"


@respx.mock
async def test_get_bytes_wraps_connection_error_as_provider_error() -> None:
    respx.get("https://example.test/image").mock(side_effect=httpx.ConnectError("connection refused"))
    client = ProviderHttpClient("pollinations", "https://example.test")

    with pytest.raises(ProviderRequestError):
        await client.get_bytes("/image")


@respx.mock
async def test_get_bytes_raises_on_error_status() -> None:
    respx.get("https://example.test/image").mock(return_value=httpx.Response(500))
    client = ProviderHttpClient("pollinations", "https://example.test")

    with pytest.raises(ProviderRequestError):
        await client.get_bytes("/image")


@respx.mock
async def test_post_bytes_returns_raw_body() -> None:
    respx.post("https://example.test/speak").mock(return_value=httpx.Response(200, content=b"raw-audio"))
    client = ProviderHttpClient("kokoro", "https://example.test")

    result = await client.post_bytes("/speak", {"text": "hi"})

    assert result == b"raw-audio"


@respx.mock
async def test_post_bytes_wraps_connection_error_as_provider_error() -> None:
    respx.post("https://example.test/speak").mock(side_effect=httpx.ConnectError("connection refused"))
    client = ProviderHttpClient("kokoro", "https://example.test")

    with pytest.raises(ProviderRequestError):
        await client.post_bytes("/speak", {"text": "hi"})
