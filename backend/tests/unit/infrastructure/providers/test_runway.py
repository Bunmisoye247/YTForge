from __future__ import annotations

import httpx
import respx

from ytforge.application.dto.video import VideoJob, VideoJobState, VideoRequest
from ytforge.infrastructure.providers.video.runway import RunwayProvider
from ytforge.infrastructure.storage.fake import FakeObjectStorage


def _request(**overrides: object) -> VideoRequest:
    defaults: dict[str, object] = {"prompt": "a cat on a skateboard", "model": "gen-3", "duration_seconds": 5.0}
    defaults.update(overrides)
    return VideoRequest(**defaults)  # type: ignore[arg-type]


def _provider(storage: FakeObjectStorage | None = None, cost_per_second_usd: float | None = None) -> RunwayProvider:
    return RunwayProvider(
        api_key="key-1", storage=storage or FakeObjectStorage(), bucket="raw-assets", cost_per_second_usd=cost_per_second_usd
    )


@respx.mock
async def test_generate_uses_text_to_video_when_no_image_reference() -> None:
    route = respx.post("https://api.runwayml.com/v1/text_to_video").mock(
        return_value=httpx.Response(200, json={"id": "task-123"})
    )
    provider = _provider()

    job = await provider.generate(_request())

    assert job.provider_job_id == "task-123"
    assert route.calls.last.request.headers["Authorization"] == "Bearer key-1"


@respx.mock
async def test_generate_uses_image_to_video_when_reference_given() -> None:
    respx.post("https://api.runwayml.com/v1/image_to_video").mock(
        return_value=httpx.Response(200, json={"id": "task-456"})
    )
    provider = _provider()

    job = await provider.generate(_request(image_reference_key="ref.png"))

    assert job.provider_job_id == "task-456"


@respx.mock
async def test_poll_returns_running_while_incomplete() -> None:
    respx.get("https://api.runwayml.com/v1/tasks/task-123").mock(
        return_value=httpx.Response(200, json={"status": "RUNNING"})
    )
    provider = _provider()

    status = await provider.poll(VideoJob(provider_job_id="task-123", model="gen-3"))

    assert status.state == VideoJobState.RUNNING
    assert status.object_key is None


@respx.mock
async def test_poll_downloads_provider_video_and_stores_it_with_duration_scaled_cost() -> None:
    respx.get("https://api.runwayml.com/v1/tasks/task-123").mock(
        return_value=httpx.Response(
            200, json={"status": "SUCCEEDED", "output": ["https://cdn.runwayml.com/output/task-123.mp4"]}
        )
    )
    respx.get("https://cdn.runwayml.com/output/task-123.mp4").mock(
        return_value=httpx.Response(200, content=b"fake-mp4-bytes")
    )
    storage = FakeObjectStorage()
    provider = _provider(storage=storage, cost_per_second_usd=0.5)

    status = await provider.poll(VideoJob(provider_job_id="task-123", model="gen-3", duration_seconds=5.0))

    assert status.state == VideoJobState.COMPLETED
    assert status.object_key is not None
    assert not status.object_key.startswith("https://")
    assert await storage.get_object("raw-assets", status.object_key) == b"fake-mp4-bytes"
    assert status.cost_usd == 2.5


@respx.mock
async def test_generate_stamps_job_with_requested_duration() -> None:
    respx.post("https://api.runwayml.com/v1/text_to_video").mock(
        return_value=httpx.Response(200, json={"id": "task-789"})
    )
    provider = _provider()

    job = await provider.generate(_request(duration_seconds=8.0))

    assert job.duration_seconds == 8.0


@respx.mock
async def test_poll_returns_failed_with_error_message() -> None:
    respx.get("https://api.runwayml.com/v1/tasks/task-123").mock(
        return_value=httpx.Response(200, json={"status": "FAILED", "failure": "content policy violation"})
    )
    provider = _provider()

    status = await provider.poll(VideoJob(provider_job_id="task-123", model="gen-3"))

    assert status.state == VideoJobState.FAILED
    assert status.error == "content policy violation"
