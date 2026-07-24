from __future__ import annotations

from ytforge.application.use_cases.videos.create_video import CreateVideoInput, create_video
from ytforge.application.use_cases.videos.list_videos import list_videos
from ytforge.application.use_cases.videos.mark_video_uploaded import mark_video_uploaded
from ytforge.application.use_cases.videos.request_publish_approval import (
    request_publish_approval,
)
from ytforge.application.use_cases.videos.update_video import UpdateVideoInput, update_video

__all__ = [
    "CreateVideoInput",
    "UpdateVideoInput",
    "create_video",
    "list_videos",
    "mark_video_uploaded",
    "request_publish_approval",
    "update_video",
]
