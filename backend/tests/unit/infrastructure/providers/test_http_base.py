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
