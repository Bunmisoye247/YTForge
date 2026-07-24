from __future__ import annotations

import hashlib

import httpx

from ytforge.application.dto.video import VideoJob, VideoJobState, VideoJobStatus, VideoRequest
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_BASE_URL = "https://api.minimax.chat/v1"
_STATE_MAP = {
    "Queueing": VideoJobState.QUEUED,
    "Processing": VideoJobState.RUNNING,
    "Success": VideoJobState.COMPLETED,
    "Fail": VideoJobState.FAILED,
}


class HailuoProvider:
    """MiniMax Hailuo video generation API — async submit-then-poll.
    # verify against current provider docs; field names below are a
    # best-effort approximation. Judgment call: the completed job only
    # gives a `file_id`, not a URL — MiniMax's actual API requires a
    # separate `/files/retrieve` call to resolve a `file_id` to a
    # `download_url`, which is what's implemented here before downloading
    # and re-uploading into our object storage (ARCHITECTURE.md §6.3)."""

    def __init__(self, api_key: str, storage: ObjectStorage, bucket: str, cost_per_second_usd: float | None = None) -> None:
        self._client = ProviderHttpClient("hailuo", _BASE_URL, {"Authorization": f"Bearer {api_key}"})
        self._storage = storage
        self._bucket = bucket
        self._cost_per_second = cost_per_second_usd

    async def generate(self, req: VideoRequest) -> VideoJob:
        async with record_provider_call("hailuo", "video.generate"):
            submit = await self._client.post_json(
                "/video_generation", {"model": req.model, "prompt": req.prompt}
            )
            return VideoJob(provider_job_id=submit["task_id"], model=req.model, duration_seconds=req.duration_seconds)

    async def poll(self, job: VideoJob) -> VideoJobStatus:
        async with record_provider_call("hailuo", "video.poll") as metric:
            body = await self._client.get_json(
                "/query/video_generation", {"task_id": job.provider_job_id}
            )
            state = _STATE_MAP.get(body["status"], VideoJobState.RUNNING)
            if state != VideoJobState.COMPLETED:
                return VideoJobStatus(state=state, error=body.get("base_resp", {}).get("status_msg"))
            file_id = body["file_id"]
            object_key = await self._download_and_store(file_id)
            cost = self._estimate_cost(job.duration_seconds)
            metric.cost_usd = cost
            return VideoJobStatus(state=state, object_key=object_key, cost_usd=cost)

    async def _download_and_store(self, file_id: str) -> str:
        retrieve = await self._client.get_json("/files/retrieve", {"file_id": file_id})
        download_url = retrieve["file"]["download_url"]
        async with httpx.AsyncClient() as client:
            response = await client.get(download_url, timeout=httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0))
            response.raise_for_status()
            data = response.content
        digest = hashlib.sha256(data).hexdigest()[:16]
        key = f"hailuo/{digest}.mp4"
        await self._storage.put_object(self._bucket, key, data, "video/mp4")
        return key

    def _estimate_cost(self, duration_seconds: float) -> float | None:
        if self._cost_per_second is None:
            return None
        return round(self._cost_per_second * duration_seconds, 6)
