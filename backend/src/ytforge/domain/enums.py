from __future__ import annotations

import enum


class ChannelRole(enum.StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class ProjectStatus(enum.StrEnum):
    IDEA = "idea"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TrendSource(enum.StrEnum):
    GOOGLE_TRENDS = "google_trends"
    YOUTUBE_TRENDING = "youtube_trending"
    REDDIT = "reddit"
    HACKER_NEWS = "hacker_news"
    X = "x"
    RSS = "rss"
    NEWS_API = "news_api"


class ScriptStatus(enum.StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class FactCheckVerdict(enum.StrEnum):
    PASSED = "passed"
    FLAGGED = "flagged"


class StoryboardStatus(enum.StrEnum):
    DRAFT = "draft"
    READY = "ready"
    APPROVED = "approved"


class AssetType(enum.StrEnum):
    IMAGE = "image"
    CLIP = "clip"
    AUDIO = "audio"
    MUSIC = "music"
    THUMBNAIL = "thumbnail"
    RENDER = "render"


class AssetStatus(enum.StrEnum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"
    ORPHANED = "orphaned"


class VoiceProfileStatus(enum.StrEnum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REVOKED = "revoked"


class PromptRunStatus(enum.StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class VideoStatus(enum.StrEnum):
    DRAFT = "draft"
    UPLOADED = "uploaded"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class ApprovalKind(enum.StrEnum):
    PUBLISH = "publish"
    SCHEDULE = "schedule"
    VOICE_CLONING = "voice_cloning"
    ASSET_DELETION = "asset_deletion"
    # Not one of CLAUDE.md's 4 "mandatory" gates, but ARCHITECTURE.md
    # §5.1's pipeline diagram routes a flagged FactCheck to a HumanReview
    # gate before Storyboard — reuses the same Approval/signal-wait
    # mechanism as the mandatory gates rather than a separate ad hoc pause.
    SCRIPT_REVIEW = "script_review"


class ApprovalStatus(enum.StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class JobStatus(enum.StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


class OutboxStatus(enum.StrEnum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


class ModelCapability(enum.StrEnum):
    LLM = "llm"
    IMAGE = "image"
    VIDEO = "video"
    TTS = "tts"
    MUSIC = "music"
    EMBEDDING = "embedding"


class ModelAvailability(enum.StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
