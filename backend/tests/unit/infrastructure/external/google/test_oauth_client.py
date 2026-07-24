from __future__ import annotations

import httpx
import respx

from ytforge.infrastructure.external.google.oauth_client import GoogleOAuthClient


def _client() -> GoogleOAuthClient:
    return GoogleOAuthClient(
        client_id="client-1", client_secret="secret-1", redirect_uri="http://localhost:8000/callback"
    )


def test_build_authorize_url_includes_required_params() -> None:
    url = _client().build_authorize_url(state="csrf-token-123")

    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "client_id=client-1" in url
    assert "state=csrf-token-123" in url
    assert "access_type=offline" in url
    assert "youtube.upload" in url


@respx.mock
async def test_exchange_code_returns_tokens() -> None:
    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(
            200, json={"access_token": "access-1", "expires_in": 3600, "refresh_token": "refresh-1"}
        )
    )

    result = await _client().exchange_code("auth-code-1")

    assert result.access_token == "access-1"
    assert result.refresh_token == "refresh-1"
    assert result.expires_in == 3600


@respx.mock
async def test_exchange_code_sends_grant_type_authorization_code() -> None:
    route = respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "a", "expires_in": 3600, "refresh_token": "r"})
    )

    await _client().exchange_code("auth-code-1")

    sent = dict(x.split("=") for x in route.calls.last.request.content.decode().split("&"))
    assert sent["grant_type"] == "authorization_code"
    assert sent["code"] == "auth-code-1"


@respx.mock
async def test_refresh_access_token_returns_new_access_token_without_refresh_token() -> None:
    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "access-2", "expires_in": 3600})
    )

    result = await _client().refresh_access_token("refresh-1")

    assert result.access_token == "access-2"
    assert result.refresh_token is None


@respx.mock
async def test_fetch_my_channel_id_returns_first_item_id() -> None:
    respx.get("https://www.googleapis.com/youtube/v3/channels").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "UC-my-channel-id"}]})
    )

    channel_id = await _client().fetch_my_channel_id("access-1")

    assert channel_id == "UC-my-channel-id"
