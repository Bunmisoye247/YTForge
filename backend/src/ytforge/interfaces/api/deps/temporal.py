from __future__ import annotations

from fastapi import HTTPException, Request, status
from temporalio.client import Client


def get_optional_temporal_client(request: Request) -> Client | None:
    """For call sites where Temporal is a nice-to-have (signaling a
    workflow after an approval decision) rather than the point of the
    request — the DB decision must still succeed even if no workflow is
    listening or Temporal isn't reachable."""
    client: Client | None = request.app.state.temporal_client
    return client


def get_temporal_client(request: Request) -> Client:
    """Reads the client created once at app startup (see `api.main`'s
    lifespan) — connecting per-request would be wasteful, and the client
    is a thin gRPC-channel wrapper safe to share across requests. `None`
    means Temporal wasn't reachable at boot (not required for most of the
    API) — surfaced as a 503 rather than a 500 crash."""
    client: Client | None = request.app.state.temporal_client
    if client is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Temporal is not reachable")
    return client
