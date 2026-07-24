// Mirrors backend/src/ytforge/domain/enums.py — keep in sync by hand until
// Phase 6+ introduces a generated-client step.

export const ChannelRole = {
  OWNER: "owner",
  ADMIN: "admin",
  EDITOR: "editor",
  VIEWER: "viewer",
} as const;
export type ChannelRole = (typeof ChannelRole)[keyof typeof ChannelRole];

export const ProjectStatus = {
  IDEA: "idea",
  IN_PROGRESS: "in_progress",
  IN_REVIEW: "in_review",
  COMPLETED: "completed",
  ARCHIVED: "archived",
} as const;
export type ProjectStatus = (typeof ProjectStatus)[keyof typeof ProjectStatus];

export const TrendSource = {
  GOOGLE_TRENDS: "google_trends",
  YOUTUBE_TRENDING: "youtube_trending",
  REDDIT: "reddit",
  HACKER_NEWS: "hacker_news",
  X: "x",
  RSS: "rss",
  NEWS_API: "news_api",
} as const;
export type TrendSource = (typeof TrendSource)[keyof typeof TrendSource];

export const ScriptStatus = {
  DRAFT: "draft",
  IN_REVIEW: "in_review",
  APPROVED: "approved",
  REJECTED: "rejected",
} as const;
export type ScriptStatus = (typeof ScriptStatus)[keyof typeof ScriptStatus];

export const FactCheckVerdict = {
  PASSED: "passed",
  FLAGGED: "flagged",
} as const;
export type FactCheckVerdict = (typeof FactCheckVerdict)[keyof typeof FactCheckVerdict];

export const StoryboardStatus = {
  DRAFT: "draft",
  READY: "ready",
  APPROVED: "approved",
} as const;
export type StoryboardStatus = (typeof StoryboardStatus)[keyof typeof StoryboardStatus];

export const AssetType = {
  IMAGE: "image",
  CLIP: "clip",
  AUDIO: "audio",
  MUSIC: "music",
  THUMBNAIL: "thumbnail",
  RENDER: "render",
} as const;
export type AssetType = (typeof AssetType)[keyof typeof AssetType];

export const AssetStatus = {
  PENDING: "pending",
  READY: "ready",
  FAILED: "failed",
  ORPHANED: "orphaned",
} as const;
export type AssetStatus = (typeof AssetStatus)[keyof typeof AssetStatus];

export const VoiceProfileStatus = {
  PENDING_APPROVAL: "pending_approval",
  APPROVED: "approved",
  REVOKED: "revoked",
} as const;
export type VoiceProfileStatus = (typeof VoiceProfileStatus)[keyof typeof VoiceProfileStatus];

export const PromptRunStatus = {
  SUCCEEDED: "succeeded",
  FAILED: "failed",
} as const;
export type PromptRunStatus = (typeof PromptRunStatus)[keyof typeof PromptRunStatus];

export const VideoStatus = {
  DRAFT: "draft",
  UPLOADED: "uploaded",
  SCHEDULED: "scheduled",
  PUBLISHED: "published",
  FAILED: "failed",
} as const;
export type VideoStatus = (typeof VideoStatus)[keyof typeof VideoStatus];

export const ApprovalKind = {
  PUBLISH: "publish",
  SCHEDULE: "schedule",
  VOICE_CLONING: "voice_cloning",
  ASSET_DELETION: "asset_deletion",
} as const;
export type ApprovalKind = (typeof ApprovalKind)[keyof typeof ApprovalKind];

export const ApprovalStatus = {
  PENDING: "pending",
  APPROVED: "approved",
  REJECTED: "rejected",
} as const;
export type ApprovalStatus = (typeof ApprovalStatus)[keyof typeof ApprovalStatus];

export const JobStatus = {
  RUNNING: "running",
  COMPLETED: "completed",
  FAILED: "failed",
  TERMINATED: "terminated",
  TIMED_OUT: "timed_out",
  CANCELLED: "cancelled",
} as const;
export type JobStatus = (typeof JobStatus)[keyof typeof JobStatus];

export const ModelCapability = {
  LLM: "llm",
  IMAGE: "image",
  VIDEO: "video",
  TTS: "tts",
  MUSIC: "music",
  EMBEDDING: "embedding",
} as const;
export type ModelCapability = (typeof ModelCapability)[keyof typeof ModelCapability];

export const ModelAvailability = {
  AVAILABLE: "available",
  UNAVAILABLE: "unavailable",
} as const;
export type ModelAvailability = (typeof ModelAvailability)[keyof typeof ModelAvailability];
