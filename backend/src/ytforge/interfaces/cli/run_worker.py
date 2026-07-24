from __future__ import annotations

import logging

from temporalio.contrib.opentelemetry import TracingInterceptor
from temporalio.worker import Worker

from ytforge.infrastructure.config.settings import get_settings
from ytforge.infrastructure.telemetry.otel_setup import configure_otel
from ytforge.infrastructure.temporal.client import build_temporal_client
from ytforge.interfaces.activities import ALL_ACTIVITIES
from ytforge.interfaces.workflows import ALL_WORKFLOWS

logger = logging.getLogger("ytforge.worker")


async def run_worker() -> None:
    """The `worker` deployable unit (ARCHITECTURE.md §1/§13): runs
    workflows + agent activities on the main task queue. Rendering
    (FFmpeg) and the outbox relay are separate deployable units —
    `run-renderer`/`run-relay` — each its own container/task queue so
    CPU-heavy rendering and event relay scale independently of this
    I/O-bound worker."""
    settings = get_settings()
    configure_otel(settings.observability)
    client = await build_temporal_client(settings.temporal)

    worker = Worker(
        client,
        task_queue=settings.temporal.task_queue,
        workflows=ALL_WORKFLOWS,
        activities=ALL_ACTIVITIES,
        interceptors=[TracingInterceptor()],
    )

    logger.info("starting ytforge worker on task queue %r", settings.temporal.task_queue)
    await worker.run()
