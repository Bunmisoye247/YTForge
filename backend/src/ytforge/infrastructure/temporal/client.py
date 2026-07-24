from __future__ import annotations

from temporalio.client import Client
from temporalio.contrib.opentelemetry import TracingInterceptor

from ytforge.infrastructure.config.settings import TemporalSettings


async def build_temporal_client(settings: TemporalSettings) -> Client:
    """`TracingInterceptor` (ARCHITECTURE.md §9's workflow -> activity ->
    provider-call trace span) must be on both the client that starts/
    signals workflows AND the `Worker` that executes them for full context
    propagation — this is the one piece of OTel instrumentation that
    can't live inside workflow code itself (which must stay deterministic;
    creating spans directly would read wall-clock time non-deterministically
    on replay). It's always attached — a no-op when `configure_otel()`
    never ran, per the OTel API's own no-op-tracer default."""
    return await Client.connect(
        settings.host, namespace=settings.namespace, interceptors=[TracingInterceptor()]
    )
