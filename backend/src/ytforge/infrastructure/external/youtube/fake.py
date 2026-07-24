from __future__ import annotations

import hashlib

from ytforge.application.dto.youtube import YouTubeUploadRequest, YouTubeUploadResult


class FakeYouTubeGateway:
    """Deterministic stand-in for `YouTubeDataApiGateway` — no Google
    OAuth server or real YouTube account needed, matching every other
    fake/real split in this codebase (`YTFORGE__MODELS__PROVIDER_SET=fake`)."""

    async def upload_video(self, req: YouTubeUploadRequest) -> YouTubeUploadResult:
        digest = hashlib.sha256(f"{req.channel_id}:{req.render_object_key}".encode()).hexdigest()[:11]
        return YouTubeUploadResult(youtube_video_id=f"fake{digest}", quota_units_consumed=1600)
