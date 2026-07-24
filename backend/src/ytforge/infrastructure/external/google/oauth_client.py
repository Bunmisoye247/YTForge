from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"

# youtube.upload: resumable video uploads. youtube.readonly +
# yt-analytics.readonly: channel identity lookup + Analytics API reads.
_SCOPES = (
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
)


@dataclass(frozen=True, slots=True)
class GoogleTokenResponse:
    access_token: str
    expires_in: int
    refresh_token: str | None = None


class GoogleOAuthClient:
    """Google OAuth2 authorization-code flow for linking a channel's
    YouTube account (ARCHITECTURE.md §7.1). No `google-auth`/`google-api-
    python-client` SDK — plain REST calls via httpx, matching this
    project's existing provider-adapter convention (CLAUDE.md: "never call
    vendor SDKs from use cases"). The actual browser consent step can't be
    exercised in this dev environment (no registered Google Cloud OAuth
    app here) — this is verified via respx-mocked token-exchange tests
    only, same honesty ceiling as Phase 6's provider adapters."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def build_authorize_url(self, state: str) -> str:
        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "response_type": "code",
            "scope": " ".join(_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{_AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> GoogleTokenResponse:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                _TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "redirect_uri": self._redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            body = response.json()
        return GoogleTokenResponse(
            access_token=body["access_token"],
            expires_in=body["expires_in"],
            refresh_token=body.get("refresh_token"),
        )

    async def refresh_access_token(self, refresh_token: str) -> GoogleTokenResponse:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                _TOKEN_URL,
                data={
                    "refresh_token": refresh_token,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            body = response.json()
        return GoogleTokenResponse(access_token=body["access_token"], expires_in=body["expires_in"])

    async def fetch_my_channel_id(self, access_token: str) -> str:
        """Resolves the linked Google account's own YouTube channel id
        right after OAuth completes, so `link_youtube_channel` has a real
        `youtube_channel_id` to store rather than leaving it null."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                _CHANNELS_URL,
                params={"part": "id", "mine": "true"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            body = response.json()
        channel_id: str = body["items"][0]["id"]
        return channel_id
