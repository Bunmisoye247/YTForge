from __future__ import annotations

import httpx
import pytest
import respx

from ytforge.application.dto.youtube import YouTubeUploadRequest
from ytforge.infrastructure.external.google.oauth_client import GoogleOAuthClient
from ytforge.infrastructure.external.youtube.data_api import YouTubeDataApiGateway
from ytforge.infrastructure.storage.fake import FakeObjectStorage


def _gateway(storage: FakeObjectStorage) -> YouTubeDataApiGateway:
    oauth_client = GoogleOAuthClient(client_id="c", client_secret="s", redirect_uri="http://localhost/callback")
    return YouTubeDataApiGateway(oauth_client, storage, "renders", quota_cost=1600)


def _request(**overrides: object) -> YouTubeUploadRequest:
    defaults: dict[str, object] = {
        "channel_id": "chan-1",
        "render_object_key": "proj-1/final.mp4",
        "title": "My Video",
        "description": "A description",
        "synthetic_content_disclosure": True,
        "refresh_token": "refresh-token-1",
    }
    defaults.update(overrides)
    return YouTubeUploadRequest(**defaults)  # type: ignore[arg-type]


@respx.mock
async def test_upload_video_returns_video_id_and_quota_cost() -> None:
    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "access-1", "expires_in": 3600})
    )
    respx.post("https://www.googleapis.com/upload/youtube/v3/videos").mock(
        return_value=httpx.Response(200, headers={"Location": "https://upload.example/session-1"})
    )
    respx.put("https://upload.example/session-1").mock(return_value=httpx.Response(200, json={"id": "yt-video-1"}))

    storage = FakeObjectStorage()
    await storage.put_object("renders", "proj-1/final.mp4", b"video-bytes", "video/mp4")

    result = await _gateway(storage).upload_video(_request())

    assert result.youtube_video_id == "yt-video-1"
    assert result.quota_units_consumed == 1600


@respx.mock
async def test_upload_video_sends_synthetic_disclosure_and_uses_fresh_access_token() -> None:
    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "fresh-access-token", "expires_in": 3600})
    )
    initiate_route = respx.post("https://www.googleapis.com/upload/youtube/v3/videos").mock(
        return_value=httpx.Response(200, headers={"Location": "https://upload.example/session-2"})
    )
    upload_route = respx.put("https://upload.example/session-2").mock(
        return_value=httpx.Response(200, json={"id": "yt-video-2"})
    )

    storage = FakeObjectStorage()
    await storage.put_object("renders", "proj-1/final.mp4", b"video-bytes", "video/mp4")

    await _gateway(storage).upload_video(_request(synthetic_content_disclosure=True))

    import json

    body = json.loads(initiate_route.calls.last.request.content)
    assert body["status"]["containsSyntheticMedia"] is True
    assert initiate_route.calls.last.request.headers["Authorization"] == "Bearer fresh-access-token"
    assert upload_route.calls.last.request.headers["Authorization"] == "Bearer fresh-access-token"
    assert upload_route.calls.last.request.content == b"video-bytes"


@respx.mock
async def test_upload_video_raises_on_upload_session_failure() -> None:
    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "access-1", "expires_in": 3600})
    )
    respx.post("https://www.googleapis.com/upload/youtube/v3/videos").mock(return_value=httpx.Response(401))

    storage = FakeObjectStorage()
    await storage.put_object("renders", "proj-1/final.mp4", b"video-bytes", "video/mp4")

    with pytest.raises(httpx.HTTPStatusError):
        await _gateway(storage).upload_video(_request())
