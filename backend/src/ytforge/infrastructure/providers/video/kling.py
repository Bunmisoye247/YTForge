from __future__ import annotations

import hashlib

import httpx

from ytforge.application.dto.video import VideoJob, VideoJobState, VideoJobStatus, VideoRequest
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_BASE_URL = "https://api.klingai.com/v1"
_STATE_MAP = {
    "submitted": VideoJobState.QUEUED,
    "processing": VideoJobState.RUNNING,
    "succeed": VideoJobState.COMPLETED,
    "failed": VideoJobState.FAILED,
}


class KlingProvider:
    """Kuaishou Kling AI video generation API — async submit-then-poll.
    # verify against current provider docs; field names below are a
    # best-effort approximation. The completed task's video `url` is
    # provider-hosted — downloaded and re-uploaded into our object storage
    # (ARCHITECTURE.md §6.3) rather than returned as-is."""

    def __init__(self, api_key: str, storage: ObjectStorage, bucket: str, cost_per_second_usd: float | None = None) -> None:
        self._client = ProviderHttpClient("kling", _BASE_URL, {"Authorization": f"Bearer {api_key}"})
        self._storage = storage
        self._bucket = bucket
        self._cost_per_second = cost_per_second_usd

    async def generate(self, req: VideoRequest) -> VideoJob:
        async with record_provider_call("kling", "video.generate"):
            submit = await self._client.post_json(
                "/videos/text2video",
                {"model_name": req.model, "prompt": req.prompt, "duration": str(int(req.duration_seconds))},
            )
            return VideoJob(
                provider_job_id=submit["data"]["task_id"], model=req.model, duration_seconds=req.duration_seconds
            )

    async def poll(self, job: VideoJob) -> VideoJobStatus:
        async with record_provider_call("kling", "video.poll") as metric:
            body = await self._client.get_json(f"/videos/text2video/{job.provider_job_id}")
            data = body["data"]
            state = _STATE_MAP.get(data["task_status"], VideoJobState.RUNNING)
            if state != VideoJobState.COMPLETED:
                return VideoJobStatus(state=state, error=data.get("task_status_msg"))
            provider_url = data["task_result"]["videos"][0]["url"]
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
        key = f"kling/{digest}.mp4"
        await self._storage.put_object(self._bucket, key, data, "video/mp4")
        return key

    async def health_check(self) -> None:
        # No documented lightweight status endpoint — bare-root probe.
        # # verify against current provider docs.
        await self._client.ping("/")

    def _estimate_cost(self, duration_seconds: float) -> float | None:
        if self._cost_per_second is None:
            return None
        return round(self._cost_per_second * duration_seconds, 6)
