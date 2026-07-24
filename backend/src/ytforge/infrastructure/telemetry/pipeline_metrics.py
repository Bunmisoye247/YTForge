from __future__ import annotations

from ytforge.infrastructure.telemetry.otel_setup import get_meter

_meter = get_meter("ytforge.pipeline")

# ARCHITECTURE.md §9's remaining named metrics not covered by
# provider_metrics.py's per-adapter-call instruments. Recorded from
# activities/agents (interfaces layer), never from workflow code — see
# the note in interfaces/workflows/video_production.py and
# temporal/client.py about why spans/metrics can't be created directly
# inside deterministic workflow bodies.
job_failures = _meter.create_counter(
    "ytforge.pipeline.job.failures", description="Terminal job failures, by workflow_type"
)
dlq_moves = _meter.create_counter(
    "ytforge.events.dlq.moves", description="Messages moved to the dead-letter stream"
)
quota_remaining = _meter.create_gauge(
    "ytforge.youtube.quota.remaining", description="Remaining daily YouTube API quota units, by channel"
)
