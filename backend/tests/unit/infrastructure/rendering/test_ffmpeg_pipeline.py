from __future__ import annotations

import pytest

from ytforge.application.dto.editing import EditingRequest, EditingSceneInput
from ytforge.infrastructure.rendering import ffmpeg_pipeline as ffmpeg_pipeline_module
from ytforge.infrastructure.rendering.ffmpeg_pipeline import (
    FFmpegEditingPipeline,
    FFmpegRenderError,
)
from ytforge.infrastructure.storage.fake import FakeObjectStorage


class _FakeProcess:
    def __init__(self, returncode: int, stderr: bytes = b"") -> None:
        self.returncode = returncode
        self._stderr = stderr

    async def communicate(self) -> tuple[bytes, bytes]:
        return b"", self._stderr


@pytest.fixture(autouse=True)
def _fake_ffmpeg(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    """Every ffmpeg invocation just writes a small placeholder file at the
    output path (the last arg) and reports success — verifies the
    pipeline's orchestration (which files get created, in what order,
    what gets uploaded) without needing a real ffmpeg binary."""
    calls: list[list[str]] = []

    async def fake_exec(*args: str, **kwargs: object):  # type: ignore[no-untyped-def]
        calls.append(list(args))
        out_path = args[-1]
        with open(out_path, "wb") as f:  # noqa: ASYNC230 - test fixture, not real async code
            f.write(b"fake-media-bytes")
        return _FakeProcess(returncode=0)

    monkeypatch.setattr(ffmpeg_pipeline_module.asyncio, "create_subprocess_exec", fake_exec)
    return calls


def _scene(index: int, visual_key: str, voice_key: str | None = None) -> EditingSceneInput:
    return EditingSceneInput(
        scene_id=f"scene-{index}",
        sequence_index=index,
        visual_object_key=visual_key,
        voice_object_key=voice_key,
        duration_seconds=4.0,
    )


async def test_render_uploads_final_video_and_returns_key() -> None:
    storage = FakeObjectStorage()
    await storage.put_object("raw-assets", "img-0.png", b"image-bytes", "image/png")
    await storage.put_object("raw-assets", "voice-0.wav", b"voice-bytes", "audio/wav")
    pipeline = FFmpegEditingPipeline(storage, "raw-assets", "renders")

    req = EditingRequest(
        project_id="proj-1",
        scenes=[_scene(0, "img-0.png", "voice-0.wav")],
    )
    result = await pipeline.render(req)

    assert result.render_object_key.startswith("proj-1/")
    assert result.render_object_key.endswith(".mp4")
    assert result.duration_seconds == 4.0
    stored = await storage.get_object("renders", result.render_object_key)
    assert stored == b"fake-media-bytes"


async def test_render_mixes_music_when_present(_fake_ffmpeg: list[list[str]]) -> None:
    storage = FakeObjectStorage()
    await storage.put_object("raw-assets", "img-0.png", b"image-bytes", "image/png")
    await storage.put_object("raw-assets", "music.mp3", b"music-bytes", "audio/mpeg")
    pipeline = FFmpegEditingPipeline(storage, "raw-assets", "renders")

    req = EditingRequest(project_id="proj-2", scenes=[_scene(0, "img-0.png")], music_object_key="music.mp3")
    await pipeline.render(req)

    # scene render + concat + music mix == 3 ffmpeg invocations
    assert len(_fake_ffmpeg) == 3
    assert "amix" in " ".join(_fake_ffmpeg[-1])


async def test_render_raises_on_nonzero_ffmpeg_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    async def failing_exec(*args: str, **kwargs: object):  # type: ignore[no-untyped-def]
        return _FakeProcess(returncode=1, stderr=b"invalid data found")

    monkeypatch.setattr(ffmpeg_pipeline_module.asyncio, "create_subprocess_exec", failing_exec)

    storage = FakeObjectStorage()
    await storage.put_object("raw-assets", "img-0.png", b"image-bytes", "image/png")
    pipeline = FFmpegEditingPipeline(storage, "raw-assets", "renders")

    with pytest.raises(FFmpegRenderError, match="invalid data found"):
        await pipeline.render(EditingRequest(project_id="proj-3", scenes=[_scene(0, "img-0.png")]))
