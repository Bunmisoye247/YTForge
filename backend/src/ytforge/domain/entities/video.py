from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from ytforge.domain.enums import VideoStatus
from ytforge.domain.errors import InvalidTransitionError

_LEGAL_TRANSITIONS: dict[VideoStatus, frozenset[VideoStatus]] = {
    VideoStatus.DRAFT: frozenset({VideoStatus.UPLOADED, VideoStatus.FAILED}),
    VideoStatus.UPLOADED: frozenset({VideoStatus.SCHEDULED, VideoStatus.PUBLISHED, VideoStatus.FAILED}),
    VideoStatus.SCHEDULED: frozenset({VideoStatus.PUBLISHED, VideoStatus.FAILED}),
    VideoStatus.PUBLISHED: frozenset(),
    VideoStatus.FAILED: frozenset({VideoStatus.DRAFT}),
}


@dataclass(slots=True, kw_only=True)
class Video:
    id: uuid.UUID
    project_id: uuid.UUID
    render_asset_id: uuid.UUID
    title: str
    description: str
    status: VideoStatus
    created_at: datetime
    updated_at: datetime
    synthetic_content_disclosure: bool = True
    youtube_video_id: str | None = None
    scheduled_publish_at: datetime | None = None
    published_at: datetime | None = None

    def transition_to(self, status: VideoStatus) -> None:
        """Uploaded/scheduled/published transitions are only ever driven by
        Phase-8 code (the YouTube upload adapter) — Phase-4 use cases only
        ever create/update DRAFT videos."""
        if status not in _LEGAL_TRANSITIONS[self.status]:
            raise InvalidTransitionError("Video", self.status.value, status.value)
        self.status = status
