from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class YouTubeUploadRequest:
    channel_id: str
    render_object_key: str
    title: str
    description: str
    synthetic_content_disclosure: bool
    refresh_token: str
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class YouTubeUploadResult:
    youtube_video_id: str
    quota_units_consumed: int
