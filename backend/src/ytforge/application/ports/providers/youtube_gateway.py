from __future__ import annotations

from typing import Protocol

from ytforge.application.dto.youtube import YouTubeUploadRequest, YouTubeUploadResult


class YouTubeGateway(Protocol):
    """Real implementation (OAuth + Data API v3 upload + quota debit) lands
    in Phase 8. Phase 6's `PublisherAgent` is built against this port now so
    its orchestration logic doesn't change shape when Phase 8 fills it in."""

    async def upload_video(self, req: YouTubeUploadRequest) -> YouTubeUploadResult: ...
