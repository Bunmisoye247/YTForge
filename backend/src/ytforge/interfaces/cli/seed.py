from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select

from ytforge.domain.enums import (
    ApprovalKind,
    ApprovalStatus,
    AssetStatus,
    AssetType,
    ChannelRole,
    FactCheckVerdict,
    JobStatus,
    ModelAvailability,
    ModelCapability,
    OutboxStatus,
    ProjectStatus,
    PromptRunStatus,
    ScriptStatus,
    StoryboardStatus,
    TrendSource,
    VideoStatus,
    VoiceProfileStatus,
)
from ytforge.infrastructure.db.models import (
    AnalyticsDailyMetric,
    AnalyticsRetentionPoint,
    AnalyticsTrafficSource,
    ApiQuotaLedger,
    Approval,
    Asset,
    AuditLog,
    Channel,
    ChannelMember,
    FactCheck,
    Job,
    ModelRegistryEntry,
    OutboxEvent,
    Project,
    PromptRun,
    PromptTemplate,
    PromptVersion,
    ResearchDocument,
    Scene,
    Script,
    SeoMetadata,
    Storyboard,
    Trend,
    User,
    Video,
    Voiceover,
    VoiceProfile,
)
from ytforge.infrastructure.db.session import session_scope
from ytforge.infrastructure.security.passwords import hash_password

SEED_USER_EMAIL = "founder@ytforge.dev"


async def seed() -> None:
    async with session_scope() as session:
        existing = await session.scalar(select(User).where(User.email == SEED_USER_EMAIL))
        if existing is not None:
            print(f"Seed data already present (user {SEED_USER_EMAIL} exists) — skipping.")
            return

        now = datetime.now(UTC)

        user = User(
            email=SEED_USER_EMAIL,
            hashed_password=hash_password("changeme123"),
            full_name="Founding Operator",
            is_active=True,
            is_superuser=True,
        )
        session.add(user)
        await session.flush()

        channel = Channel(
            name="Everyday AI Explainers",
            youtube_channel_id="UCseedchannel0001",
            brand_kit={"primary_color": "#0EA5E9", "font": "Inter", "logo_object_key": None},
            defaults={"language": "en", "default_duration_seconds": 480},
        )
        session.add(channel)
        await session.flush()

        session.add(ChannelMember(channel_id=channel.id, user_id=user.id, role=ChannelRole.OWNER))

        trend = Trend(
            channel_id=channel.id,
            source=TrendSource.GOOGLE_TRENDS,
            topic="on-device AI models",
            url="https://trends.google.com/trends/explore?q=on-device+ai",
            score=87.5,
            raw_payload={"region": "US", "rising": True},
        )
        session.add(trend)
        await session.flush()

        project = Project(
            channel_id=channel.id,
            trend_id=trend.id,
            created_by_user_id=user.id,
            title="Why On-Device AI Is About to Change Everything",
            status=ProjectStatus.IN_PROGRESS,
            budget_usd=150.00,
        )
        session.add(project)
        await session.flush()

        research_doc = ResearchDocument(
            project_id=project.id,
            source_url="https://example.com/on-device-ai-report",
            title="State of On-Device AI 2026",
            content="On-device models now run multi-billion parameter LLMs locally with NPUs...",
            citation={"author": "Example Research Lab", "year": 2026},
            qdrant_point_id=str(uuid.uuid4()),
            published_at=now - timedelta(days=10),
        )
        session.add(research_doc)

        script = Script(
            project_id=project.id,
            version=1,
            status=ScriptStatus.APPROVED,
            sections={
                "hook": "Your phone just got smarter without sending a single byte to the cloud.",
                "body": ["Section 1: what changed", "Section 2: why it matters", "Section 3: what's next"],
                "cta": "Subscribe for more on-device AI breakdowns.",
            },
            model_used="anthropic/claude-sonnet-4-6",
            token_count=2140,
        )
        session.add(script)
        await session.flush()

        session.add(
            FactCheck(
                script_id=script.id,
                script_version=script.version,
                verdict=FactCheckVerdict.PASSED,
                flags=[],
                model_used="openai/gpt-4.1",
            )
        )

        storyboard = Storyboard(
            project_id=project.id, script_id=script.id, status=StoryboardStatus.READY
        )
        session.add(storyboard)
        await session.flush()

        scene_one = Scene(
            storyboard_id=storyboard.id,
            sequence_index=0,
            description="Close-up of a phone screen running a local LLM offline.",
            duration_seconds=8.0,
            image_prompt="macro shot of smartphone screen, glowing neural network overlay",
            video_prompt="slow push-in on phone screen, airplane mode icon visible",
            voice_line="Your phone just got smarter without sending a single byte to the cloud.",
        )
        scene_two = Scene(
            storyboard_id=storyboard.id,
            sequence_index=1,
            description="Split screen comparing cloud round-trip vs on-device latency.",
            duration_seconds=10.0,
            image_prompt="split screen infographic, cloud vs chip icon, latency bars",
            video_prompt="animated bar chart racing, cloud icon vs chip icon",
            voice_line="Section 1: what changed",
        )
        session.add_all([scene_one, scene_two])
        await session.flush()

        image_asset = Asset(
            project_id=project.id,
            scene_id=scene_one.id,
            asset_type=AssetType.IMAGE,
            status=AssetStatus.READY,
            bucket="raw-assets",
            object_key=f"{channel.id}/{project.id}/image/{scene_one.id}.png",
            checksum_sha256="a" * 64,
            provenance={"provider": "flux_api", "model": "flux-1.1-pro"},
        )
        thumbnail_asset = Asset(
            project_id=project.id,
            asset_type=AssetType.THUMBNAIL,
            status=AssetStatus.READY,
            bucket="thumbnails",
            object_key=f"{channel.id}/{project.id}/thumbnail/main.png",
            checksum_sha256="b" * 64,
            provenance={"provider": "flux_api", "model": "flux-1.1-pro"},
        )
        audio_asset = Asset(
            project_id=project.id,
            scene_id=scene_one.id,
            asset_type=AssetType.AUDIO,
            status=AssetStatus.READY,
            bucket="raw-assets",
            object_key=f"{channel.id}/{project.id}/audio/narration.wav",
            checksum_sha256="c" * 64,
            provenance={"provider": "elevenlabs", "voice_id": "seed-voice"},
        )
        render_asset = Asset(
            project_id=project.id,
            asset_type=AssetType.RENDER,
            status=AssetStatus.READY,
            bucket="renders",
            object_key=f"{channel.id}/{project.id}/render/final.mp4",
            checksum_sha256="d" * 64,
            provenance={"provider": "ffmpeg_pipeline"},
        )
        session.add_all([image_asset, thumbnail_asset, audio_asset, render_asset])
        await session.flush()

        voice_profile = VoiceProfile(
            channel_id=channel.id,
            name="Narrator — Warm Male",
            provider="elevenlabs",
            provider_voice_id="seed-voice",
            status=VoiceProfileStatus.APPROVED,
            consent_artifact_object_key=f"{channel.id}/consent/voice-profile-seed.pdf",
            consent_recorded_at=now - timedelta(days=30),
        )
        session.add(voice_profile)
        await session.flush()

        session.add(
            Voiceover(
                project_id=project.id,
                scene_id=scene_one.id,
                voice_profile_id=voice_profile.id,
                asset_id=audio_asset.id,
                transcript="Your phone just got smarter without sending a single byte to the cloud.",
                word_timestamps=[{"word": "Your", "start": 0.0, "end": 0.2}],
                duration_seconds=8.0,
            )
        )

        prompt_template = PromptTemplate(agent="writer", name="video_script")
        session.add(prompt_template)
        await session.flush()

        prompt_version = PromptVersion(
            template_id=prompt_template.id,
            version=1,
            content="You are writing a YouTube script about {{ topic }}...",
            front_matter={"version": 1, "model_hints": ["anthropic/claude-sonnet-4-6"]},
            model_hints={"primary": "anthropic/claude-sonnet-4-6"},
            variables={"topic": "string", "research_context": "string"},
        )
        session.add(prompt_version)
        await session.flush()

        session.add(
            PromptRun(
                prompt_version_id=prompt_version.id,
                project_id=project.id,
                input_variables={"topic": "on-device AI models"},
                rendered_prompt="You are writing a YouTube script about on-device AI models...",
                response="{...structured script json...}",
                model_used="anthropic/claude-sonnet-4-6",
                status=PromptRunStatus.SUCCEEDED,
                latency_ms=4200,
                cost_usd=0.0842,
            )
        )

        video = Video(
            project_id=project.id,
            render_asset_id=render_asset.id,
            youtube_video_id="dQw4w9WgXcQ",
            title="Why On-Device AI Is About to Change Everything",
            description="On-device AI models are catching up fast. Here's what changed and why it matters.",
            synthetic_content_disclosure=True,
            status=VideoStatus.PUBLISHED,
            scheduled_publish_at=now - timedelta(days=2),
            published_at=now - timedelta(days=2),
        )
        session.add(video)
        await session.flush()

        session.add(
            SeoMetadata(
                video_id=video.id,
                thumbnail_asset_id=thumbnail_asset.id,
                title="Why On-Device AI Is About to Change Everything",
                description="On-device AI models are catching up fast. Here's what changed and why it matters.",
                tags=["on-device ai", "local llm", "npu", "edge ai"],
                chapters=[{"title": "Intro", "start_seconds": 0}, {"title": "What changed", "start_seconds": 45}],
                keywords=["on-device ai", "local llm"],
            )
        )

        session.add(
            Approval(
                kind=ApprovalKind.PUBLISH,
                status=ApprovalStatus.APPROVED,
                payload={"video_id": str(video.id)},
                workflow_id="video-production-seed-0001",
                requested_by_user_id=user.id,
                decided_by_user_id=user.id,
                decided_at=now - timedelta(days=2, hours=1),
                note="Looks good, ship it.",
            )
        )

        session.add(
            AnalyticsDailyMetric(
                video_id=video.id,
                date=date.today() - timedelta(days=1),
                views=12450,
                watch_time_minutes=38210.5,
                likes=980,
                comments=64,
                shares=112,
                subscribers_gained=45,
                revenue_usd=87.32,
            )
        )
        session.add(
            AnalyticsRetentionPoint(
                video_id=video.id,
                date=date.today() - timedelta(days=1),
                elapsed_video_percent=50.0,
                audience_retention_percent=62.5,
            )
        )
        session.add(
            AnalyticsTrafficSource(
                video_id=video.id,
                date=date.today() - timedelta(days=1),
                source_type="suggested_videos",
                views=6100,
                watch_time_minutes=19800.0,
            )
        )

        session.add(
            Job(
                temporal_workflow_id="video-production-seed-0001",
                temporal_run_id=str(uuid.uuid4()),
                workflow_type="VideoProductionWorkflow",
                project_id=project.id,
                status=JobStatus.COMPLETED,
                started_at=now - timedelta(days=3),
                completed_at=now - timedelta(days=2),
                last_heartbeat_at=now - timedelta(days=2),
            )
        )

        session.add(
            OutboxEvent(
                aggregate_type="video",
                aggregate_id=video.id,
                event_type="VideoPublished",
                payload={"video_id": str(video.id), "youtube_video_id": video.youtube_video_id},
                status=OutboxStatus.PUBLISHED,
                published_at=now - timedelta(days=2),
            )
        )

        session.add(
            AuditLog(
                actor_user_id=user.id,
                action="video.published",
                entity_type="video",
                entity_id=video.id,
                before={"status": "uploaded"},
                after={"status": "published"},
                ip_address="127.0.0.1",
            )
        )

        session.add(
            ModelRegistryEntry(
                provider="anthropic",
                model_name="claude-sonnet-4-6",
                capability=ModelCapability.LLM,
                base_url=None,
                status=ModelAvailability.AVAILABLE,
                discovered_at=now - timedelta(days=30),
                last_checked_at=now,
                entry_metadata={"context_window": 200000},
            )
        )

        session.add(
            ApiQuotaLedger(
                channel_id=channel.id,
                date=date.today() - timedelta(days=2),
                operation="video_upload",
                units_consumed=1600,
                units_budget=10000,
            )
        )

        print(f"Seeded 1 user, 1 channel, 1 project pipeline (project_id={project.id}).")
