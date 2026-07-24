from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Plain dataclasses only, and deliberately a top-level sibling of
# `interfaces.activities` rather than nested inside it: Temporal's
# workflow sandbox re-imports a workflow file's entire import graph to
# validate it, and `interfaces.activities.__init__` pulls in the real
# activity implementations (sqlalchemy, httpx, `Path(__file__).resolve()`
# at module scope in `interfaces.agents.factory`, etc). Importing
# `interfaces.activities.dto` would still run `interfaces/activities/
# __init__.py` first (Python always initializes a package before any of
# its submodules) and trip the sandbox's restricted-call detector. Living
# here means workflow files never touch that package at all.


@dataclass(frozen=True, slots=True)
class RunAgentInput:
    agent_name: str
    project_id: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RunAgentOutput:
    ok: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass(frozen=True, slots=True)
class RecordJobStartedActivityInput:
    workflow_id: str
    run_id: str
    workflow_type: str
    project_id: str | None = None


@dataclass(frozen=True, slots=True)
class RecordJobStartedActivityOutput:
    job_id: str


@dataclass(frozen=True, slots=True)
class UpdateJobStatusActivityInput:
    job_id: str
    status: str
    error: str | None = None


@dataclass(frozen=True, slots=True)
class EmitEventActivityInput:
    aggregate_type: str
    aggregate_id: str
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RequestApprovalActivityInput:
    kind: str
    requested_by_user_id: str
    workflow_id: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RequestApprovalActivityOutput:
    approval_id: str


@dataclass(frozen=True, slots=True)
class OrphanAssetsActivityInput:
    asset_ids: list[str]


@dataclass(frozen=True, slots=True)
class CreateVideoActivityInput:
    project_id: str
    render_asset_id: str
    title: str
    description: str


@dataclass(frozen=True, slots=True)
class CreateVideoActivityOutput:
    video_id: str


@dataclass(frozen=True, slots=True)
class RequestPublishApprovalActivityInput:
    video_id: str
    requested_by_user_id: str
    workflow_id: str


@dataclass(frozen=True, slots=True)
class RequestPublishApprovalActivityOutput:
    approval_id: str


@dataclass(frozen=True, slots=True)
class CheckBudgetActivityInput:
    project_id: str


@dataclass(frozen=True, slots=True)
class CheckBudgetActivityOutput:
    is_exhausted: bool
    spent_usd: str
    budget_usd: str | None


@dataclass(frozen=True, slots=True)
class FetchCandidateTopicsActivityInput:
    limit: int = 10


@dataclass(frozen=True, slots=True)
class FetchCandidateTopicsActivityOutput:
    topics: list[str]


@dataclass(frozen=True, slots=True)
class IngestAnalyticsActivityInput:
    video_id: str
    target_date_iso: str


@dataclass(frozen=True, slots=True)
class IngestAnalyticsActivityOutput:
    ingested: bool
