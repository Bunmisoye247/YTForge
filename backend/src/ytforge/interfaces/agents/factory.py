from __future__ import annotations

from pathlib import Path

from ytforge.application.ports.providers import UnitOfWork
from ytforge.infrastructure.config.settings import Settings
from ytforge.infrastructure.external.google.oauth_client import GoogleOAuthClient
from ytforge.infrastructure.external.youtube.data_api import YouTubeDataApiGateway
from ytforge.infrastructure.external.youtube.fake import FakeYouTubeGateway
from ytforge.infrastructure.prompts.jinja_store import FilesystemPromptStore
from ytforge.infrastructure.providers.fakeprovider import FakeSearchProvider
from ytforge.infrastructure.providers.registry import build_fake_registries, build_real_registries
from ytforge.infrastructure.providers.router import ConfigDrivenModelRouter
from ytforge.infrastructure.rendering.fake import FakeEditingPipeline
from ytforge.infrastructure.rendering.ffmpeg_pipeline import FFmpegEditingPipeline
from ytforge.infrastructure.storage.fake import FakeObjectStorage
from ytforge.infrastructure.storage.minio_storage import MinioObjectStorage
from ytforge.infrastructure.vector.fake import FakeVectorStore
from ytforge.infrastructure.vector.qdrant import QdrantVectorStore
from ytforge.interfaces.agents.context import AgentContext
from ytforge.interfaces.agents.tools import (
    CalculatorTool,
    QdrantRetrievalTool,
    ToolRegistry,
    WebSearchTool,
    YouTubeLookupTool,
)

PROMPTS_DIR = Path(__file__).resolve().parents[4] / "prompts"


def build_agent_context(settings: Settings, uow: UnitOfWork) -> AgentContext:
    """Shared provider/tool/pipeline wiring — used by both the
    `run-agent`/`sync-prompts` CLI path and the Temporal activity that runs
    agents, so the two invocation paths (manual CLI, real workflow) can
    never drift apart."""
    is_fake = settings.models.provider_set == "fake"

    object_storage = (
        FakeObjectStorage()
        if is_fake
        else MinioObjectStorage(
            settings.minio.endpoint,
            settings.minio.access_key,
            settings.minio.secret_key.get_secret_value(),
            settings.minio.secure,
        )
    )
    raw_assets_bucket = settings.minio.buckets["raw_assets"]

    registries = (
        build_fake_registries()
        if is_fake
        else build_real_registries(settings.providers, object_storage, raw_assets_bucket)
    )
    model_router = ConfigDrivenModelRouter(settings.models.routes, registries)

    vector_store = FakeVectorStore() if is_fake else QdrantVectorStore(settings.qdrant.url)

    editing_pipeline = (
        FakeEditingPipeline()
        if is_fake
        else FFmpegEditingPipeline(object_storage, raw_assets_bucket, settings.minio.buckets["renders"])
    )

    youtube_gateway = (
        FakeYouTubeGateway()
        if is_fake
        else YouTubeDataApiGateway(
            GoogleOAuthClient(
                settings.google_oauth.client_id,
                settings.google_oauth.client_secret.get_secret_value(),
                settings.google_oauth.redirect_uri,
            ),
            object_storage,
            settings.minio.buckets["renders"],
            settings.youtube.upload_quota_cost,
        )
    )

    # WebSearchTool has no real adapter yet (see FakeSearchProvider) —
    # always fake-backed regardless of provider_set.
    tools = ToolRegistry(
        [
            CalculatorTool(),
            WebSearchTool(FakeSearchProvider()),
            QdrantRetrievalTool(vector_store),
            YouTubeLookupTool(),
        ]
    )

    return AgentContext(
        model_router=model_router,
        tools=tools,
        prompts=FilesystemPromptStore(PROMPTS_DIR),
        uow=uow,
        vector_store=vector_store,
        object_storage=object_storage,
        editing_pipeline=editing_pipeline,
        youtube_gateway=youtube_gateway,
        youtube_upload_quota_cost=settings.youtube.upload_quota_cost,
        youtube_daily_quota_budget=settings.youtube.daily_quota_budget,
    )
