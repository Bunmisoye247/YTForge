"""initial schema

Revision ID: 20260722_0001
Revises:
Create Date: 2026-07-22

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260722_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "channels",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("youtube_channel_id", sa.String(length=64), nullable=True),
        sa.Column("brand_kit", postgresql.JSONB(), nullable=False),
        sa.Column("defaults", postgresql.JSONB(), nullable=False),
        sa.Column("oauth_refresh_token_ciphertext", sa.LargeBinary(), nullable=True),
        sa.Column("oauth_refresh_token_nonce", sa.LargeBinary(), nullable=True),
        sa.Column("data_key_ciphertext", sa.LargeBinary(), nullable=True),
        sa.Column("encryption_key_version", sa.Integer(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("youtube_channel_id", name="uq_channels_youtube_channel_id"),
    )

    op.create_table(
        "model_registry",
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column(
            "capability",
            postgresql.ENUM("llm", "image", "video", "tts", "music", "embedding", name="model_capability"),
            nullable=False,
        ),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("available", "unavailable", name="model_availability"),
            nullable=False,
        ),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("entry_metadata", postgresql.JSONB(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider", "model_name", "capability", name="uq_model_registry_provider_model_cap"
        ),
    )

    op.create_table(
        "outbox",
        sa.Column("aggregate_type", sa.String(length=128), nullable=False),
        sa.Column("aggregate_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "status", postgresql.ENUM("pending", "published", "failed", name="outbox_status"), nullable=False
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outbox_event_type", "outbox", ["event_type"], unique=False)

    op.create_table(
        "prompt_templates",
        sa.Column("agent", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent", "name", name="uq_prompt_templates_agent_name"),
    )

    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "api_quota_ledger",
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("units_consumed", sa.Integer(), nullable=False),
        sa.Column("units_budget", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_api_quota_ledger_date", "api_quota_ledger", ["date"], unique=False)

    op.create_table(
        "approvals",
        sa.Column(
            "kind",
            postgresql.ENUM("publish", "schedule", "voice_cloning", "asset_deletion", name="approval_kind"),
            nullable=False,
        ),
        sa.Column(
            "status", postgresql.ENUM("pending", "approved", "rejected", name="approval_status"), nullable=False
        ),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("workflow_id", sa.String(length=255), nullable=True),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("decided_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["decided_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=128), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("before", postgresql.JSONB(), nullable=True),
        sa.Column("after", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "channel_members",
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "role", postgresql.ENUM("owner", "admin", "editor", "viewer", name="channel_role"), nullable=False
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("channel_id", "user_id", name="uq_channel_members_channel_user"),
    )

    op.create_table(
        "prompt_versions",
        sa.Column("template_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("front_matter", postgresql.JSONB(), nullable=False),
        sa.Column("model_hints", postgresql.JSONB(), nullable=False),
        sa.Column("variables", postgresql.JSONB(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["template_id"], ["prompt_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", "version", name="uq_prompt_versions_template_version"),
    )

    op.create_table(
        "trends",
        sa.Column("channel_id", sa.Uuid(), nullable=True),
        sa.Column(
            "source",
            postgresql.ENUM(
                "google_trends",
                "youtube_trending",
                "reddit",
                "hacker_news",
                "x",
                "rss",
                "news_api",
                name="trend_source",
            ),
            nullable=False,
        ),
        sa.Column("topic", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "voice_profiles",
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_voice_id", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("pending_approval", "approved", "revoked", name="voice_profile_status"),
            nullable=False,
        ),
        sa.Column("consent_artifact_object_key", sa.String(length=1024), nullable=False),
        sa.Column("consent_recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "projects",
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column("trend_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "idea", "in_progress", "in_review", "completed", "archived", name="project_status"
            ),
            nullable=False,
        ),
        sa.Column("budget_usd", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trend_id"], ["trends.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "jobs",
        sa.Column("temporal_workflow_id", sa.String(length=255), nullable=False),
        sa.Column("temporal_run_id", sa.String(length=255), nullable=False),
        sa.Column("workflow_type", sa.String(length=255), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "running", "completed", "failed", "terminated", "timed_out", "cancelled", name="job_status"
            ),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_temporal_workflow_id", "jobs", ["temporal_workflow_id"], unique=False)

    op.create_table(
        "prompt_runs",
        sa.Column("prompt_version_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("input_variables", postgresql.JSONB(), nullable=False),
        sa.Column("rendered_prompt", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("model_used", sa.String(length=128), nullable=False),
        sa.Column("status", postgresql.ENUM("succeeded", "failed", name="prompt_run_status"), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["prompt_version_id"], ["prompt_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "research_documents",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citation", postgresql.JSONB(), nullable=False),
        sa.Column("qdrant_point_id", sa.String(length=64), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "scripts",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("draft", "in_review", "approved", "rejected", name="script_status"),
            nullable=False,
        ),
        sa.Column("sections", postgresql.JSONB(), nullable=False),
        sa.Column("model_used", sa.String(length=128), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "version", name="uq_scripts_project_version"),
    )

    op.create_table(
        "fact_checks",
        sa.Column("script_id", sa.Uuid(), nullable=False),
        sa.Column("script_version", sa.Integer(), nullable=False),
        sa.Column("verdict", postgresql.ENUM("passed", "flagged", name="fact_check_verdict"), nullable=False),
        sa.Column("flags", postgresql.JSONB(), nullable=False),
        sa.Column("model_used", sa.String(length=128), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["script_id"], ["scripts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "storyboards",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("script_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status", postgresql.ENUM("draft", "ready", "approved", name="storyboard_status"), nullable=False
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["script_id"], ["scripts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "scenes",
        sa.Column("storyboard_id", sa.Uuid(), nullable=False),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("duration_seconds", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("image_prompt", sa.Text(), nullable=True),
        sa.Column("video_prompt", sa.Text(), nullable=True),
        sa.Column("voice_line", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["storyboard_id"], ["storyboards.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storyboard_id", "sequence_index", name="uq_scenes_storyboard_sequence"),
    )

    op.create_table(
        "assets",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("scene_id", sa.Uuid(), nullable=True),
        sa.Column(
            "asset_type",
            postgresql.ENUM("image", "clip", "audio", "music", "thumbnail", "render", name="asset_type"),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM("pending", "ready", "failed", "orphaned", name="asset_status"),
            nullable=False,
        ),
        sa.Column("bucket", sa.String(length=63), nullable=False),
        sa.Column("object_key", sa.String(length=1024), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("provenance", postgresql.JSONB(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["scene_id"], ["scenes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "videos",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("render_asset_id", sa.Uuid(), nullable=False),
        sa.Column("youtube_video_id", sa.String(length=32), nullable=True),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("synthetic_content_disclosure", sa.Boolean(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("draft", "uploaded", "scheduled", "published", "failed", name="video_status"),
            nullable=False,
        ),
        sa.Column("scheduled_publish_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["render_asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("youtube_video_id", name="uq_videos_youtube_video_id"),
    )

    op.create_table(
        "voiceovers",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("scene_id", sa.Uuid(), nullable=True),
        sa.Column("voice_profile_id", sa.Uuid(), nullable=True),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=False),
        sa.Column("word_timestamps", postgresql.JSONB(), nullable=False),
        sa.Column("duration_seconds", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["scene_id"], ["scenes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["voice_profile_id"], ["voice_profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "analytics_daily_metrics",
        sa.Column("video_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("views", sa.Integer(), nullable=False),
        sa.Column("watch_time_minutes", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("likes", sa.Integer(), nullable=False),
        sa.Column("comments", sa.Integer(), nullable=False),
        sa.Column("shares", sa.Integer(), nullable=False),
        sa.Column("subscribers_gained", sa.Integer(), nullable=False),
        sa.Column("revenue_usd", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("video_id", "date", name="uq_analytics_daily_metrics_video_date"),
    )

    op.create_table(
        "analytics_retention_points",
        sa.Column("video_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("elapsed_video_percent", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("audience_retention_percent", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "video_id", "date", "elapsed_video_percent", name="uq_analytics_retention_video_date_pct"
        ),
    )

    op.create_table(
        "analytics_traffic_sources",
        sa.Column("video_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("views", sa.Integer(), nullable=False),
        sa.Column("watch_time_minutes", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "video_id", "date", "source_type", name="uq_analytics_traffic_video_date_source"
        ),
    )

    op.create_table(
        "seo_metadata",
        sa.Column("video_id", sa.Uuid(), nullable=False),
        sa.Column("thumbnail_asset_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=5000), nullable=False),
        sa.Column("tags", postgresql.JSONB(), nullable=False),
        sa.Column("chapters", postgresql.JSONB(), nullable=False),
        sa.Column("keywords", postgresql.JSONB(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["thumbnail_asset_id"], ["assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("video_id", name="uq_seo_metadata_video_id"),
    )


def downgrade() -> None:
    op.drop_table("seo_metadata")
    op.drop_table("analytics_traffic_sources")
    op.drop_table("analytics_retention_points")
    op.drop_table("analytics_daily_metrics")
    op.drop_table("voiceovers")
    op.drop_table("videos")
    op.drop_table("assets")
    op.drop_table("scenes")
    op.drop_table("storyboards")
    op.drop_table("fact_checks")
    op.drop_table("scripts")
    op.drop_table("research_documents")
    op.drop_table("prompt_runs")
    op.drop_index("ix_jobs_temporal_workflow_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_table("projects")
    op.drop_table("voice_profiles")
    op.drop_table("trends")
    op.drop_table("prompt_versions")
    op.drop_table("channel_members")
    op.drop_table("audit_logs")
    op.drop_table("approvals")
    op.drop_index("ix_api_quota_ledger_date", table_name="api_quota_ledger")
    op.drop_table("api_quota_ledger")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("prompt_templates")
    op.drop_index("ix_outbox_event_type", table_name="outbox")
    op.drop_table("outbox")
    op.drop_table("model_registry")
    op.drop_table("channels")

    bind = op.get_bind()
    postgresql.ENUM("llm", "image", "video", "tts", "music", "embedding", name="model_capability").drop(
        bind, checkfirst=True
    )
    postgresql.ENUM("available", "unavailable", name="model_availability").drop(bind, checkfirst=True)
    postgresql.ENUM("pending", "published", "failed", name="outbox_status").drop(bind, checkfirst=True)
    postgresql.ENUM(
        "publish", "schedule", "voice_cloning", "asset_deletion", name="approval_kind"
    ).drop(bind, checkfirst=True)
    postgresql.ENUM("pending", "approved", "rejected", name="approval_status").drop(bind, checkfirst=True)
    postgresql.ENUM("owner", "admin", "editor", "viewer", name="channel_role").drop(bind, checkfirst=True)
    postgresql.ENUM(
        "google_trends",
        "youtube_trending",
        "reddit",
        "hacker_news",
        "x",
        "rss",
        "news_api",
        name="trend_source",
    ).drop(bind, checkfirst=True)
    postgresql.ENUM(
        "pending_approval", "approved", "revoked", name="voice_profile_status"
    ).drop(bind, checkfirst=True)
    postgresql.ENUM(
        "idea", "in_progress", "in_review", "completed", "archived", name="project_status"
    ).drop(bind, checkfirst=True)
    postgresql.ENUM(
        "running", "completed", "failed", "terminated", "timed_out", "cancelled", name="job_status"
    ).drop(bind, checkfirst=True)
    postgresql.ENUM("succeeded", "failed", name="prompt_run_status").drop(bind, checkfirst=True)
    postgresql.ENUM(
        "draft", "in_review", "approved", "rejected", name="script_status"
    ).drop(bind, checkfirst=True)
    postgresql.ENUM("passed", "flagged", name="fact_check_verdict").drop(bind, checkfirst=True)
    postgresql.ENUM("draft", "ready", "approved", name="storyboard_status").drop(bind, checkfirst=True)
    postgresql.ENUM(
        "image", "clip", "audio", "music", "thumbnail", "render", name="asset_type"
    ).drop(bind, checkfirst=True)
    postgresql.ENUM(
        "pending", "ready", "failed", "orphaned", name="asset_status"
    ).drop(bind, checkfirst=True)
    postgresql.ENUM(
        "draft", "uploaded", "scheduled", "published", "failed", name="video_status"
    ).drop(bind, checkfirst=True)
