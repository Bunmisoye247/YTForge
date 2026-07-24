from __future__ import annotations

import httpx

from ytforge.application.dto.youtube import YouTubeUploadRequest, YouTubeUploadResult
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.external.google.oauth_client import GoogleOAuthClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
_UPLOAD_TIMEOUT = httpx.Timeout(connect=10.0, read=300.0, write=300.0, pool=10.0)


class YouTubeDataApiGateway:
    """Real YouTube Data API v3 resumable upload (ARCHITECTURE.md §3/§8) —
    plain httpx REST calls, no `google-api-python-client` SDK (CLAUDE.md:
    "never call vendor SDKs from use cases"). Exchanges the channel's
    stored refresh token for a fresh access token, fetches the render's
    bytes from object storage, then does the two-step resumable-upload
    protocol (initiate session -> PUT bytes).

    # verify against current API docs: `status.containsSyntheticMedia`
    is YouTube's 2024 AI-disclosure field name at time of writing — the
    exact field name is worth re-confirming against current docs before
    a real upload, same honesty flag as Phase 6's under-documented
    provider adapters. Nothing here can be exercised against a real
    YouTube account in this environment regardless."""

    def __init__(
        self, oauth_client: GoogleOAuthClient, storage: ObjectStorage, renders_bucket: str, quota_cost: int
    ) -> None:
        self._oauth_client = oauth_client
        self._storage = storage
        self._renders_bucket = renders_bucket
        self._quota_cost = quota_cost

    async def upload_video(self, req: YouTubeUploadRequest) -> YouTubeUploadResult:
        async with record_provider_call("youtube_data_api", "videos.insert"):
            access_token = (await self._oauth_client.refresh_access_token(req.refresh_token)).access_token
            video_bytes = await self._storage.get_object(self._renders_bucket, req.render_object_key)

            metadata = {
                "snippet": {"title": req.title, "description": req.description, "tags": req.tags},
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False,
                    "containsSyntheticMedia": req.synthetic_content_disclosure,
                },
            }
            headers = {"Authorization": f"Bearer {access_token}"}

            async with httpx.AsyncClient(timeout=_UPLOAD_TIMEOUT) as client:
                initiate = await client.post(
                    _UPLOAD_URL,
                    params={"uploadType": "resumable", "part": "snippet,status"},
                    headers={**headers, "X-Upload-Content-Type": "video/mp4"},
                    json=metadata,
                )
                initiate.raise_for_status()
                upload_url = initiate.headers["Location"]

                upload = await client.put(
                    upload_url, headers={**headers, "Content-Type": "video/mp4"}, content=video_bytes
                )
                upload.raise_for_status()
                body = upload.json()

            # Cost here is quota units, not USD — recorded via the
            # api_quota_ledger (PublisherAgent), not the telemetry layer.
            return YouTubeUploadResult(youtube_video_id=body["id"], quota_units_consumed=self._quota_cost)
