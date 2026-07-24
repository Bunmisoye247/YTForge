from __future__ import annotations

import logging

from temporalio.contrib.opentelemetry import TracingInterceptor
from temporalio.worker import Worker

from ytforge.infrastructure.config.settings import get_settings
from ytforge.infrastructure.telemetry.otel_setup import configure_otel
from ytforge.infrastructure.temporal.client import build_temporal_client
from ytforge.interfaces.activities import ALL_ACTIVITIES

logger = logging.getLogger("ytforge.renderer")


async def run_renderer() -> None:
    """The `renderer` deployable unit (ARCHITECTURE.md §1/§13) — same
    activity code as `worker` (the `editing` agent runs through the same
    generic `run_agent` activity as every other agent), but listening on
    its own task queue so `VideoProductionWorkflow` can route the FFmpeg-
    heavy editing step here specifically (`Dockerfile.renderer` installs
    ffmpeg/fonts/media libs; the plain `worker` image doesn't need them).
    Activity-only worker — it never executes workflow code, so no
    `workflows=` registration."""
    settings = get_settings()
    configure_otel(settings.observability)
    client = await build_temporal_client(settings.temporal)

    worker = Worker(
        client,
        task_queue=settings.temporal.renderer_task_queue,
        activities=ALL_ACTIVITIES,
        interceptors=[TracingInterceptor()],
    )

    logger.info("starting ytforge renderer on task queue %r", settings.temporal.renderer_task_queue)
    await worker.run()
