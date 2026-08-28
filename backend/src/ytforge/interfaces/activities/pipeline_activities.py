from __future__ import annotations

import asyncio
import uuid
from datetime import date as date_
from decimal import Decimal

from temporalio import activity

from ytforge.application.common.budget_meter import check_budget
from ytforge.application.common.errors import InvalidStateError, NotFoundError
from ytforge.application.use_cases.analytics import IngestDailyMetricInput, ingest_daily_metric
from ytforge.application.use_cases.approvals import (
    DecideApprovalInput,
    RequestApprovalInput,
    decide_approval,
    request_approval,
)
from ytforge.application.use_cases.assets import orphan_asset
from ytforge.application.use_cases.jobs import (
    RecordJobStartedInput,
    record_job_started,
    update_job_status,
)
from ytforge.application.use_cases.videos import (
    CreateVideoInput,
    create_video,
    request_publish_approval,
)
from ytforge.domain.enums import ApprovalKind, ApprovalStatus, JobStatus
from ytforge.infrastructure.config.settings import ModelRoute, Settings, get_settings
from ytforge.infrastructure.db.session import get_session_factory
from ytforge.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from ytforge.infrastructure.external.google.oauth_client import GoogleOAuthClient
from ytforge.infrastructure.external.trends_sources.fake import FakeTrendSource
from ytforge.infrastructure.external.trends_sources.hackernews import HackerNewsTrendSource
from ytforge.infrastructure.external.youtube.analytics_api import (
    AnalyticsMetricsResult,
    YouTubeAnalyticsApiClient,
)
from ytforge.infrastructure.providers.registry import (
    ProviderRegistries,
    build_fake_registries,
    build_real_registries,
)
from ytforge.infrastructure.storage.minio_storage import MinioObjectStorage
from ytforge.infrastructure.telemetry.pipeline_metrics import job_failures
from ytforge.interfaces.activity_dto import (
    CheckBudgetActivityInput,
    CheckBudgetActivityOutput,
    CreateVideoActivityInput,
    CreateVideoActivityOutput,
    EmitEventActivityInput,
    FetchCandidateTopicsActivityInput,
    FetchCandidateTopicsActivityOutput,
    IngestAnalyticsActivityInput,
    IngestAnalyticsActivityOutput,
    OrphanAssetsActivityInput,
    PreflightCheckActivityInput,
    PreflightCheckActivityOutput,
    RecordJobStartedActivityInput,
    RecordJobStartedActivityOutput,
    RequestApprovalActivityInput,
    RequestApprovalActivityOutput,
    RequestPublishApprovalActivityInput,
    RequestPublishApprovalActivityOutput,
    UpdateJobStatusActivityInput,
)

# route_name -> which ProviderRegistries collection resolves it (mirrors
# ConfigDrivenModelRouter's per-capability methods: embeddings still goes
# through `.llm` since embed() is part of LLMProvider, not a separate
# registry). Only the routes VideoProductionWorkflow's agents actually
# reference (writer/image/video agents' prompt-refinement step also uses
# script_writing, not a dedicated route) — trend_scoring/analytics_insights/
# music_generation belong to other workflows, not this one.
_PREFLIGHT_ROUTES: dict[str, str] = {
    "research_summary": "llm",
    "embeddings": "llm",
    "script_writing": "llm",
    "fact_checking": "llm",
    "storyboard": "llm",
    "voice_direction": "llm",
    "seo": "llm",
    "image_generation": "image",
    "video_generation": "video",
    "voice_synthesis": "tts",
}


def _split_provider_model(provider_model: str) -> tuple[str, str]:
    provider, _, model = provider_model.partition("/")
    return provider, model


def _build_registries(settings: Settings) -> ProviderRegistries:
    if settings.models.provider_set == "fake":
        return build_fake_registries()
    object_storage = MinioObjectStorage(
        settings.minio.endpoint,
        settings.minio.access_key,
        settings.minio.secret_key.get_secret_value(),
        settings.minio.secure,
    )
    return build_real_registries(settings.providers, object_storage, settings.minio.buckets["raw_assets"])


async def _check_one_provider(registry_kind: str, provider_key: str, registries: ProviderRegistries) -> str | None:
    """Returns None on success, else a short reason string — never raises,
    so one provider's failure can't break the concurrent gather."""
    provider = getattr(registries, registry_kind).get(provider_key)
    if provider is None:
        return "not configured"
    try:
        await provider.health_check()
    except Exception as exc:  # reduced to a message and returned, not swallowed
        return str(exc)
    return None


@activity.defn(name="record_job_started")
async def record_job_started_activity(data: RecordJobStartedActivityInput) -> RecordJobStartedActivityOutput:
    uow = SqlAlchemyUnitOfWork(get_session_factory())
    async with uow:
        job = await record_job_started(
            uow,
            RecordJobStartedInput(
                temporal_workflow_id=data.workflow_id,
                temporal_run_id=data.run_id,
                workflow_type=data.workflow_type,
                project_id=uuid.UUID(data.project_id) if data.project_id else None,
            ),
        )
    return RecordJobStartedActivityOutput(job_id=str(job.id))


@activity.defn(name="update_job_status")
async def update_job_status_activity(data: UpdateJobStatusActivityInput) -> None:
    status = JobStatus(data.status)
    uow = SqlAlchemyUnitOfWork(get_session_factory())
    async with uow:
        job = await update_job_status(uow, uuid.UUID(data.job_id), status, data.error)
    if status == JobStatus.FAILED:
        job_failures.add(1, {"workflow_type": job.workflow_type})


@activity.defn(name="emit_event")
async def emit_event_activity(data: EmitEventActivityInput) -> None:
    """Generic outbox-event emitter every workflow uses for stage-transition
    events (e.g. "PipelineStageCompleted") — the relay picks these up and
    publishes to Redis Streams, which the SSE endpoint tails for the live
    pipeline tracker (ARCHITECTURE.md §5.1/§2.3)."""
    uow = SqlAlchemyUnitOfWork(get_session_factory())
    async with uow:
        await uow.add_event(
            aggregate_type=data.aggregate_type,
            aggregate_id=uuid.UUID(data.aggregate_id),
            event_type=data.event_type,
            payload=data.payload,
        )
        await uow.commit()


async def _maybe_auto_decide(uow: SqlAlchemyUnitOfWork, approval_id: uuid.UUID, requested_by_user_id: uuid.UUID) -> str | None:
    """When `pipeline.demo_auto_approve` is on, immediately approves the
    just-requested approval through the real decide_approval() path (same
    `approvals` row + `approval.decided` audit log entry a human decision
    would produce) and returns the resulting status. Returns None (leaving
    the approval PENDING) when the flag is off — the normal, non-demo path."""
    if not get_settings().pipeline.demo_auto_approve:
        return None
    approval = await decide_approval(
        uow,
        approval_id,
        DecideApprovalInput(
            status=ApprovalStatus.APPROVED,
            decided_by_user_id=requested_by_user_id,
            note="Auto-approved (demo mode: YTFORGE__PIPELINE__DEMO_AUTO_APPROVE)",
        ),
    )
    return approval.status.value


@activity.defn(name="request_approval")
async def request_approval_activity(data: RequestApprovalActivityInput) -> RequestApprovalActivityOutput:
    requested_by_user_id = uuid.UUID(data.requested_by_user_id)
    uow = SqlAlchemyUnitOfWork(get_session_factory())
    async with uow:
        approval = await request_approval(
            uow,
            RequestApprovalInput(
                kind=ApprovalKind(data.kind),
                requested_by_user_id=requested_by_user_id,
                payload=data.payload,
                workflow_id=data.workflow_id,
            ),
        )
        auto_decided_status = await _maybe_auto_decide(uow, approval.id, requested_by_user_id)
    return RequestApprovalActivityOutput(approval_id=str(approval.id), auto_decided_status=auto_decided_status)


@activity.defn(name="request_publish_approval")
async def request_publish_approval_activity(
    data: RequestPublishApprovalActivityInput,
) -> RequestPublishApprovalActivityOutput:
    """`request_publish_approval` (unlike the generic `request_approval`)
    doesn't take a `workflow_id` param directly — it's stamped on
    afterward here so the API's decision endpoint can still find and
    signal this workflow."""
    requested_by_user_id = uuid.UUID(data.requested_by_user_id)
    uow = SqlAlchemyUnitOfWork(get_session_factory())
    async with uow:
        approval = await request_publish_approval(uow, uuid.UUID(data.video_id), requested_by_user_id)
        approval.workflow_id = data.workflow_id
        await uow.approvals.update(approval)
        await uow.commit()
        auto_decided_status = await _maybe_auto_decide(uow, approval.id, requested_by_user_id)
    return RequestPublishApprovalActivityOutput(approval_id=str(approval.id), auto_decided_status=auto_decided_status)


@activity.defn(name="orphan_assets")
async def orphan_assets_activity(data: OrphanAssetsActivityInput) -> None:
    """Saga compensation (ARCHITECTURE.md §5.1): on terminal pipeline
    failure after assets were already created, soft-delete them rather
    than leaving orphaned READY rows with no owning video. Per-asset
    failures (already orphaned, not found) are skipped, not raised — this
    activity's job is best-effort cleanup, not another thing that can fail
    the failure handler."""
    uow = SqlAlchemyUnitOfWork(get_session_factory())
    async with uow:
        for asset_id_raw in data.asset_ids:
            try:
                await orphan_asset(uow, uuid.UUID(asset_id_raw))
            except (NotFoundError, InvalidStateError):
                continue


@activity.defn(name="create_video")
async def create_video_activity(data: CreateVideoActivityInput) -> CreateVideoActivityOutput:
    uow = SqlAlchemyUnitOfWork(get_session_factory())
    async with uow:
        video = await create_video(
            uow,
            CreateVideoInput(
                project_id=uuid.UUID(data.project_id),
                render_asset_id=uuid.UUID(data.render_asset_id),
                title=data.title,
                description=data.description,
            ),
        )
    return CreateVideoActivityOutput(video_id=str(video.id))


@activity.defn(name="check_budget")
async def check_budget_activity(data: CheckBudgetActivityInput) -> CheckBudgetActivityOutput:
    uow = SqlAlchemyUnitOfWork(get_session_factory())
    async with uow:
        status = await check_budget(uow, uuid.UUID(data.project_id))
    return CheckBudgetActivityOutput(
        is_exhausted=status.is_exhausted,
        spent_usd=str(status.spent_usd),
        budget_usd=str(status.budget_usd) if status.budget_usd is not None else None,
    )


@activity.defn(name="fetch_candidate_topics")
async def fetch_candidate_topics_activity(
    data: FetchCandidateTopicsActivityInput,
) -> FetchCandidateTopicsActivityOutput:
    """Feeds `TrendAgent`'s `candidate_topics` input. Picks the real
    (Hacker News) or fake source the same way `interfaces.agents.factory
    .build_agent_context` picks real-vs-fake providers."""
    settings = get_settings()
    source = FakeTrendSource() if settings.models.provider_set == "fake" else HackerNewsTrendSource()
    topics = await source.fetch_candidate_topics(limit=data.limit)
    return FetchCandidateTopicsActivityOutput(topics=topics)


@activity.defn(name="ingest_analytics")
async def ingest_analytics_activity(data: IngestAnalyticsActivityInput) -> IngestAnalyticsActivityOutput:
    """Pulls one day of real YouTube Analytics metrics for a video and
    persists them via the existing manual-ingestion use case
    (`ingest_daily_metric`) — the `AnalyticsCronWorkflow` step that
    replaces "assume metrics already exist" with "actually go get them."
    Resolves channel/refresh-token from `video_id` alone (video -> project
    -> channel, same chain `PublisherAgent` uses) rather than threading a
    refresh token through workflow input/history. Skipped, not an error,
    if the video was never uploaded (`youtube_video_id` still None) or its
    channel isn't linked."""
    settings = get_settings()
    video_id = uuid.UUID(data.video_id)
    target_date = date_.fromisoformat(data.target_date_iso)

    uow = SqlAlchemyUnitOfWork(get_session_factory())
    async with uow:
        video = await uow.videos.get_by_id(video_id)
        if video is None or video.youtube_video_id is None:
            return IngestAnalyticsActivityOutput(ingested=False)

        if settings.models.provider_set == "fake":
            metrics = AnalyticsMetricsResult(
                views=100,
                watch_time_minutes=Decimal("50"),
                likes=10,
                comments=2,
                shares=1,
                subscribers_gained=1,
                revenue_usd=Decimal("0.50"),
            )
        else:
            project = await uow.projects.get_by_id(video.project_id)
            if project is None:
                return IngestAnalyticsActivityOutput(ingested=False)
            channel = await uow.channels.get_by_id(project.channel_id)
            if channel is None or channel.oauth_refresh_token is None:
                return IngestAnalyticsActivityOutput(ingested=False)

            oauth_client = GoogleOAuthClient(
                settings.google_oauth.client_id,
                settings.google_oauth.client_secret.get_secret_value(),
                settings.google_oauth.redirect_uri,
            )
            access_token = (await oauth_client.refresh_access_token(channel.oauth_refresh_token)).access_token
            metrics = await YouTubeAnalyticsApiClient().fetch_daily_metrics(
                access_token, video.youtube_video_id, target_date
            )

        await ingest_daily_metric(
            uow,
            IngestDailyMetricInput(
                video_id=video_id,
                date=target_date,
                views=metrics.views,
                watch_time_minutes=metrics.watch_time_minutes,
                likes=metrics.likes,
                comments=metrics.comments,
                shares=metrics.shares,
                subscribers_gained=metrics.subscribers_gained,
                revenue_usd=metrics.revenue_usd,
            ),
        )
    return IngestAnalyticsActivityOutput(ingested=True)


async def _evaluate_preflight(routes: dict[str, ModelRoute], registries: ProviderRegistries) -> PreflightCheckActivityOutput:
    """Dry-runs the exact same primary/fallback resolution
    ConfigDrivenModelRouter uses at call time, but against each candidate's
    health_check() instead of a real (expensive) generation call. A route
    is healthy if ANY candidate in its chain is both configured and
    reachable — matching the router's own "first one that works"
    semantics, so pre-flight doesn't reject a run the router would have
    happily served via a fallback. Only fails when a route has NO healthy
    candidate at all — the exact case that would otherwise surface as an
    expensive-stage failure (AllProvidersExhaustedError) minutes into a
    real run instead of seconds into this one. Pure aside from the
    `health_check()` calls themselves — no `get_settings()` — so tests can
    hand it fake routes/registries directly."""
    # Dedup: the same provider (e.g. anthropic) appears in several routes'
    # chains — health-check each distinct (registry, provider) pair once,
    # concurrently, and let every route that references it reuse the result.
    candidates: dict[tuple[str, str], list[str]] = {}
    for route_name, registry_kind in _PREFLIGHT_ROUTES.items():
        route = routes.get(route_name)
        if route is None:
            continue
        for provider_model in (route.primary, *route.fallback):
            provider_key, _ = _split_provider_model(provider_model)
            candidates.setdefault((registry_kind, provider_key), []).append(route_name)

    keys = list(candidates.keys())
    results = await asyncio.gather(
        *(_check_one_provider(registry_kind, provider_key, registries) for registry_kind, provider_key in keys)
    )
    health: dict[tuple[str, str], str | None] = dict(zip(keys, results, strict=True))

    errors: list[str] = []
    for route_name, registry_kind in _PREFLIGHT_ROUTES.items():
        route = routes.get(route_name)
        if route is None:
            errors.append(f"{route_name}: no route configured")
            continue
        attempts: list[str] = []
        healthy = False
        for provider_model in (route.primary, *route.fallback):
            provider_key, _ = _split_provider_model(provider_model)
            reason = health[(registry_kind, provider_key)]
            if reason is None:
                healthy = True
                break
            attempts.append(f"{provider_key}: {reason}")
        if not healthy:
            errors.append(f"{route_name}: all candidates unhealthy ({'; '.join(attempts)})")

    return PreflightCheckActivityOutput(ok=not errors, errors=errors)


@activity.defn(name="preflight_check")
async def preflight_check_activity(data: PreflightCheckActivityInput) -> PreflightCheckActivityOutput:
    settings = get_settings()
    registries = _build_registries(settings)
    return await _evaluate_preflight(settings.models.routes, registries)
