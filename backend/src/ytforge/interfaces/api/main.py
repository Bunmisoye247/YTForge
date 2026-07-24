from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from starlette.middleware.cors import CORSMiddleware

from ytforge.infrastructure.config.settings import get_settings
from ytforge.infrastructure.telemetry.otel_setup import configure_otel
from ytforge.infrastructure.temporal.client import build_temporal_client
from ytforge.interfaces.api.middleware.errors import register_exception_handlers
from ytforge.interfaces.api.middleware.request_id import RequestIdMiddleware
from ytforge.interfaces.api.routers import (
    analytics,
    approvals,
    assets,
    audit,
    auth,
    channels,
    models,
    pipelines,
    projects,
    prompts,
    research,
    scripts,
    settings,
    storyboards,
    trends,
    videos,
    voice,
)

API_PREFIX = "/api/v1"

_ROUTERS = (
    auth.router,
    channels.router,
    projects.router,
    trends.router,
    research.router,
    scripts.router,
    storyboards.router,
    assets.router,
    voice.router,
    videos.router,
    pipelines.router,
    approvals.router,
    prompts.router,
    analytics.router,
    models.router,
    settings.router,
    audit.router,
)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    configure_otel(settings.observability)
    try:
        app.state.temporal_client = await build_temporal_client(settings.temporal)
    except Exception:
        # Temporal isn't required for most of the API (CRUD, auth, prompts,
        # analytics, …) — only the pipelines start/cancel endpoints need
        # it, and those return a clear 503 rather than the whole app
        # failing to boot because no Temporal server is running locally.
        app.state.temporal_client = None
    yield


def create_app() -> FastAPI:
    app_settings = get_settings()
    app = FastAPI(title="YTForge API", version="0.1.0", lifespan=_lifespan)

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.app.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    FastAPIInstrumentor.instrument_app(app)

    @app.get("/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        """Unversioned, unauthenticated liveness probe — what
        `deploy/compose/docker-compose.yml`'s `api` healthcheck hits.
        Deliberately shallow (process-is-up, not a DB/Redis/etc. deep
        check) since Compose already healthchecks each dependency
        directly and gates `api`'s startup on them via `depends_on`."""
        return {"status": "ok"}

    for router in _ROUTERS:
        app.include_router(router, prefix=API_PREFIX)

    return app
