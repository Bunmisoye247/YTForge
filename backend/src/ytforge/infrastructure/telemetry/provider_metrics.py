from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from opentelemetry.trace import Status, StatusCode

from ytforge.infrastructure.telemetry.otel_setup import get_meter, get_tracer

logger = logging.getLogger("ytforge.provider_metrics")

_tracer = get_tracer("ytforge.provider")
_meter = get_meter("ytforge.provider")
# ARCHITECTURE.md §9: "Prometheus metrics: pipeline stage durations,
# provider latency/error/cost counters, queue depths, render times, …".
# Stage durations and render times both come from spans (this same call
# wraps the FFmpeg render, so its span duration IS "render times" — no
# separate instrument needed); queue depths are Temporal-server-side and
# come from enabling Temporal's own Prometheus endpoint (deploy/compose),
# not from application code. These three cover provider latency/error/cost.
_latency_histogram = _meter.create_histogram(
    "ytforge.provider.call.duration", unit="ms", description="Provider adapter call latency"
)
_cost_counter = _meter.create_counter(
    "ytforge.provider.call.cost_usd", unit="usd", description="Cumulative provider spend"
)
_error_counter = _meter.create_counter(
    "ytforge.provider.call.errors", description="Provider adapter call failures"
)


@dataclass(slots=True)
class ProviderCallRecord:
    provider: str
    capability: str
    latency_ms: int = 0
    cost_usd: float | None = None
    error: str | None = None


@asynccontextmanager
async def record_provider_call(provider: str, capability: str) -> AsyncIterator[ProviderCallRecord]:
    """Every adapter method wraps its call in this (CLAUDE.md: "every
    provider adapter records cost + latency via the telemetry layer") —
    structured JSON log (unconditional) plus a real OTel span + metrics
    (Phase 10; no-op until `configure_otel()` has run, per the OTel API's
    own no-op-provider default, so this is safe to call whether or not a
    collector is configured)."""
    attributes = {"provider": provider, "capability": capability}
    record = ProviderCallRecord(provider=provider, capability=capability)
    start = time.perf_counter()
    with _tracer.start_as_current_span(f"{provider}.{capability}", attributes=attributes) as span:
        try:
            yield record
        except Exception as exc:
            record.error = str(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            _error_counter.add(1, {**attributes, "error_type": type(exc).__name__})
            raise
        finally:
            record.latency_ms = int((time.perf_counter() - start) * 1000)
            _latency_histogram.record(record.latency_ms, attributes)
            if record.cost_usd is not None:
                _cost_counter.add(record.cost_usd, attributes)
            logger.info(
                "provider_call",
                extra={"payload": json.dumps(_record_to_dict(record))},
            )


def _record_to_dict(record: ProviderCallRecord) -> dict[str, object]:
    return {
        "provider": record.provider,
        "capability": record.capability,
        "latency_ms": record.latency_ms,
        "cost_usd": record.cost_usd,
        "error": record.error,
    }
