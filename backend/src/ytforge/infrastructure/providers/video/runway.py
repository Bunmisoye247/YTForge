from __future__ import annotations

import hashlib

import httpx

from ytforge.application.dto.video import VideoJob, VideoJobState, VideoJobStatus, VideoRequest
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_BASE_URL = "https://api.dev.runwayml.com/v1"
_STATE_MAP = {
    "PENDING": VideoJobState.QUEUED,
    "THROTTLED": VideoJobState.QUEUED,
    "RUNNING": VideoJobState.RUNNING,
    "SUCCEEDED": VideoJobState.COMPLETED,
    "FAILED": VideoJobState.FAILED,
}


class RunwayProvider:
    """Runway ML API — async submit-then-poll job pattern.
    https://docs.dev.runwayml.com/ Reference pattern (Phase 7) for
    async/job-based adapters: `poll()`'s terminal response only ever gives
    a URL hosted on the PROVIDER's own CDN — that URL is downloaded and
    re-uploaded into our object storage so `Asset.object_key` never points
    at a third-party URL that can expire (ARCHITECTURE.md §6.3)."""

    def __init__(
        self, api_key: str, storage: ObjectStorage, bucket: str, cost_per_second_usd: float | None = None
    ) -> None:
        self._client = ProviderHttpClient(
            "runway", _BASE_URL, {"Authorization": f"Bearer {api_key}", "X-Runway-Version": "2024-11-06"}
        )
        self._storage = storage
        self._bucket = bucket
        self._cost_per_second = cost_per_second_usd

    async def generate(self, req: VideoRequest) -> VideoJob:
        async with record_provider_call("runway", "video.generate"):
            path = "/image_to_video" if req.image_reference_key else "/text_to_video"
            body: dict[str, object] = {
                "model": req.model,
                "promptText": req.prompt,
                "duration": req.duration_seconds,
                # Required by Runway's API; landscape is the only sensible
                # default until VideoRequest carries a per-project aspect
                # ratio (every route this adapter serves today is YouTube
                # long-form/landscape).
                "ratio": "1280:720",
            }
            if req.image_reference_key:
                body["promptImage"] = req.image_reference_key
            submit = await self._client.post_json(path, body)
            return VideoJob(provider_job_id=submit["id"], model=req.model, duration_seconds=req.duration_seconds)

    async def poll(self, job: VideoJob) -> VideoJobStatus:
        async with record_provider_call("runway", "video.poll") as metric:
            body = await self._client.get_json(f"/tasks/{job.provider_job_id}")
            state = _STATE_MAP.get(body["status"], VideoJobState.RUNNING)
            if state != VideoJobState.COMPLETED:
                return VideoJobStatus(state=state, error=body.get("failure"))

            provider_url = body["output"][0]
            object_key = await self._download_and_store(provider_url)
            cost = self._estimate_cost(job.duration_seconds)
            metric.cost_usd = cost
            return VideoJobStatus(state=state, object_key=object_key, cost_usd=cost)

    async def _download_and_store(self, provider_url: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(provider_url, timeout=httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0))
            response.raise_for_status()
            data = response.content
        digest = hashlib.sha256(data).hexdigest()[:16]
        key = f"runway/{digest}.mp4"
        await self._storage.put_object(self._bucket, key, data, "video/mp4")
        return key

    def _estimate_cost(self, duration_seconds: float) -> float | None:
        if self._cost_per_second is None:
            return None
        return round(self._cost_per_second * duration_seconds, 6)
