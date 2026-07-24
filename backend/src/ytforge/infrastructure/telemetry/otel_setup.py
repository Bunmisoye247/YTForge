from __future__ import annotations

import logging

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from ytforge.infrastructure.config.settings import ObservabilitySettings

_configured = False


def configure_otel(settings: ObservabilitySettings) -> None:
    """Wires the OTel SDK — traces + metrics + logs, all exported via OTLP
    gRPC to the collector Phase 9 stood up (ARCHITECTURE.md §9) — once,
    at process startup (api/worker/renderer each call this). A no-op when
    `otel_exporter_endpoint` is unset: no collector runs outside the
    `observability` compose profile, and instrumentation must never block
    normal operation when there's nothing to send to. Idempotent — safe to
    call more than once (e.g. import-order quirks in tests)."""
    global _configured
    if _configured or not settings.otel_exporter_endpoint:
        return

    resource = Resource.create({"service.name": settings.service_name})
    endpoint = settings.otel_exporter_endpoint

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
    )
    trace.set_tracer_provider(tracer_provider)

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[
            PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint, insecure=True))
        ],
    )
    metrics.set_meter_provider(meter_provider)

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=endpoint, insecure=True))
    )
    # Attached to the root logger — every `logging.getLogger(...)` call
    # site in this codebase (structured JSON logs already emitted by
    # provider_metrics.py etc) gets its record shipped to Loki via the
    # collector, tagged with trace_id/span_id automatically by the SDK
    # when a span is active (ARCHITECTURE.md §9's "correlated by trace id").
    logging.getLogger().addHandler(LoggingHandler(level=logging.INFO, logger_provider=logger_provider))

    _configured = True


def get_tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    return metrics.get_meter(name)
