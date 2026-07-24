from __future__ import annotations

import hashlib

import httpx

from ytforge.application.dto.video import VideoJob, VideoJobState, VideoJobStatus, VideoRequest
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_BASE_URL = "https://api.lumalabs.ai/dream-machine/v1"
_STATE_MAP = {
    "queued": VideoJobState.QUEUED,
    "dreaming": VideoJobState.RUNNING,
    "completed": VideoJobState.COMPLETED,
    "failed": VideoJobState.FAILED,
}


class LumaProvider:
    """Luma Dream Machine API — async submit-then-poll job pattern.
    # verify against current provider docs; field names below are a
    # best-effort approximation. The completed generation's `video` asset
    # is provider-hosted — downloaded and re-uploaded into our object
    # storage (ARCHITECTURE.md §6.3) rather than returned as-is."""

    def __init__(self, api_key: str, storage: ObjectStorage, bucket: str, cost_per_second_usd: float | None = None) -> None:
        self._client = ProviderHttpClient("luma", _BASE_URL, {"Authorization": f"Bearer {api_key}"})
        self._storage = storage
        self._bucket = bucket
        self._cost_per_second = cost_per_second_usd

    async def generate(self, req: VideoRequest) -> VideoJob:
        async with record_provider_call("luma", "video.generate"):
            submit = await self._client.post_json(
                "/generations", {"prompt": req.prompt, "model": req.model}
            )
            return VideoJob(provider_job_id=submit["id"], model=req.model, duration_seconds=req.duration_seconds)

    async def poll(self, job: VideoJob) -> VideoJobStatus:
        async with record_provider_call("luma", "video.poll") as metric:
            body = await self._client.get_json(f"/generations/{job.provider_job_id}")
            state = _STATE_MAP.get(body["state"], VideoJobState.RUNNING)
            if state != VideoJobState.COMPLETED:
                return VideoJobStatus(state=state, error=body.get("failure_reason"))
            provider_url = body["assets"]["video"]
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
        key = f"luma/{digest}.mp4"
        await self._storage.put_object(self._bucket, key, data, "video/mp4")
        return key

    def _estimate_cost(self, duration_seconds: float) -> float | None:
        if self._cost_per_second is None:
            return None
        return round(self._cost_per_second * duration_seconds, 6)
