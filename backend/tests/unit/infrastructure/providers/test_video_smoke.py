from __future__ import annotations

import httpx
import respx

from ytforge.application.dto.video import VideoJob, VideoJobState, VideoRequest
from ytforge.infrastructure.providers.video.hailuo import HailuoProvider
from ytforge.infrastructure.providers.video.kling import KlingProvider
from ytforge.infrastructure.providers.video.luma import LumaProvider
from ytforge.infrastructure.providers.video.veo import VeoProvider
from ytforge.infrastructure.storage.fake import FakeObjectStorage


def _request() -> VideoRequest:
    return VideoRequest(prompt="a cat on a skateboard", model="model-x", duration_seconds=5.0)


@respx.mock
async def test_veo_generate_and_poll_smoke() -> None:
    respx.post(url__regex=r"generativelanguage\.googleapis\.com/v1beta/models/model-x:generateVideo.*").mock(
        return_value=httpx.Response(200, json={"name": "operations/op-1"})
    )
    respx.get(url__regex=r"generativelanguage\.googleapis\.com/v1beta/operations/op-1.*").mock(
        return_value=httpx.Response(
            200, json={"done": True, "response": {"video": {"uri": "https://cdn/video.mp4"}}}
        )
    )
    respx.get("https://cdn/video.mp4").mock(return_value=httpx.Response(200, content=b"veo-mp4-bytes"))
    provider = VeoProvider(api_key="key-1", storage=FakeObjectStorage(), bucket="raw-assets", cost_per_second_usd=0.1)

    job = await provider.generate(_request())
    status = await provider.poll(job)

    assert job.provider_job_id == "operations/op-1"
    assert status.state == VideoJobState.COMPLETED
    assert status.object_key is not None and not status.object_key.startswith("https://")


@respx.mock
async def test_kling_generate_and_poll_smoke() -> None:
    respx.post("https://api.klingai.com/v1/videos/text2video").mock(
        return_value=httpx.Response(200, json={"data": {"task_id": "task-1"}})
    )
    respx.get("https://api.klingai.com/v1/videos/text2video/task-1").mock(
        return_value=httpx.Response(
            200,
            json={"data": {"task_status": "succeed", "task_result": {"videos": [{"url": "https://cdn/x.mp4"}]}}},
        )
    )
    respx.get("https://cdn/x.mp4").mock(return_value=httpx.Response(200, content=b"kling-mp4-bytes"))
    provider = KlingProvider(api_key="key-1", storage=FakeObjectStorage(), bucket="raw-assets", cost_per_second_usd=0.2)

    job = await provider.generate(_request())
    status = await provider.poll(job)

    assert job.provider_job_id == "task-1"
    assert status.state == VideoJobState.COMPLETED
    assert status.object_key is not None and not status.object_key.startswith("https://")


@respx.mock
async def test_luma_generate_and_poll_smoke() -> None:
    respx.post("https://api.lumalabs.ai/dream-machine/v1/generations").mock(
        return_value=httpx.Response(200, json={"id": "gen-1"})
    )
    respx.get("https://api.lumalabs.ai/dream-machine/v1/generations/gen-1").mock(
        return_value=httpx.Response(200, json={"state": "completed", "assets": {"video": "https://cdn/x.mp4"}})
    )
    respx.get("https://cdn/x.mp4").mock(return_value=httpx.Response(200, content=b"luma-mp4-bytes"))
    provider = LumaProvider(api_key="key-1", storage=FakeObjectStorage(), bucket="raw-assets", cost_per_second_usd=0.3)

    job = await provider.generate(_request())
    status = await provider.poll(job)

    assert job.provider_job_id == "gen-1"
    assert status.state == VideoJobState.COMPLETED
    assert status.object_key is not None and not status.object_key.startswith("https://")


@respx.mock
async def test_hailuo_generate_and_poll_smoke() -> None:
    respx.post("https://api.minimax.chat/v1/video_generation").mock(
        return_value=httpx.Response(200, json={"task_id": "task-1"})
    )
    respx.get("https://api.minimax.chat/v1/query/video_generation").mock(
        return_value=httpx.Response(200, json={"status": "Success", "file_id": "file-1"})
    )
    respx.get("https://api.minimax.chat/v1/files/retrieve").mock(
        return_value=httpx.Response(200, json={"file": {"download_url": "https://cdn/hailuo.mp4"}})
    )
    respx.get("https://cdn/hailuo.mp4").mock(return_value=httpx.Response(200, content=b"hailuo-mp4-bytes"))
    provider = HailuoProvider(api_key="key-1", storage=FakeObjectStorage(), bucket="raw-assets", cost_per_second_usd=0.4)

    job = await provider.generate(_request())
    status = await provider.poll(job)

    assert job.provider_job_id == "task-1"
    assert status.state == VideoJobState.COMPLETED
    assert status.object_key is not None and not status.object_key.startswith("file-")


@respx.mock
async def test_kling_poll_reports_non_terminal_state() -> None:
    respx.get("https://api.klingai.com/v1/videos/text2video/task-2").mock(
        return_value=httpx.Response(200, json={"data": {"task_status": "processing"}})
    )
    provider = KlingProvider(api_key="key-1", storage=FakeObjectStorage(), bucket="raw-assets")

    status = await provider.poll(VideoJob(provider_job_id="task-2", model="model-x"))

    assert status.state == VideoJobState.RUNNING
    assert status.object_key is None
