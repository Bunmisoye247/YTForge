from __future__ import annotations

import hashlib

import httpx

from ytforge.application.dto.video import VideoJob, VideoJobState, VideoJobStatus, VideoRequest
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
_STATE_MAP = {"PROCESSING": VideoJobState.RUNNING, "SUCCEEDED": VideoJobState.COMPLETED, "FAILED": VideoJobState.FAILED}


class VeoProvider:
    """Google Veo (video generation) API — async operation pattern.
    # verify against current provider docs; field names below are a
    # best-effort approximation. The completed operation's video `uri` is
    # hosted by Google — downloaded and re-uploaded into our object
    # storage (ARCHITECTURE.md §6.3) rather than returned as-is."""

    def __init__(self, api_key: str, storage: ObjectStorage, bucket: str, cost_per_second_usd: float | None = None) -> None:
        self._client = ProviderHttpClient("veo", _BASE_URL)
        self._api_key = api_key
        self._storage = storage
        self._bucket = bucket
        self._cost_per_second = cost_per_second_usd

    async def generate(self, req: VideoRequest) -> VideoJob:
        async with record_provider_call("veo", "video.generate"):
            submit = await self._client.post_json(
                f"/models/{req.model}:generateVideo?key={self._api_key}",
                {"prompt": req.prompt, "durationSeconds": req.duration_seconds},
            )
            return VideoJob(provider_job_id=submit["name"], model=req.model, duration_seconds=req.duration_seconds)

    async def poll(self, job: VideoJob) -> VideoJobStatus:
        async with record_provider_call("veo", "video.poll") as metric:
            body = await self._client.get_json(f"/{job.provider_job_id}?key={self._api_key}")
            done = body.get("done", False)
            if not done:
                return VideoJobStatus(state=VideoJobState.RUNNING)
            if "error" in body:
                return VideoJobStatus(state=VideoJobState.FAILED, error=str(body["error"]))
            provider_uri = body["response"]["video"]["uri"]
            object_key = await self._download_and_store(provider_uri)
            cost = self._estimate_cost(job.duration_seconds)
            metric.cost_usd = cost
            return VideoJobStatus(state=VideoJobState.COMPLETED, object_key=object_key, cost_usd=cost)

    async def _download_and_store(self, provider_uri: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                provider_uri,
                params={"key": self._api_key},
                timeout=httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0),
            )
            response.raise_for_status()
            data = response.content
        digest = hashlib.sha256(data).hexdigest()[:16]
        key = f"veo/{digest}.mp4"
        await self._storage.put_object(self._bucket, key, data, "video/mp4")
        return key

    def _estimate_cost(self, duration_seconds: float) -> float | None:
        if self._cost_per_second is None:
            return None
        return round(self._cost_per_second * duration_seconds, 6)
