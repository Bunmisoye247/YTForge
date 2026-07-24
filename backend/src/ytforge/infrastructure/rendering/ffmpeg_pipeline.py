from __future__ import annotations

import asyncio
import hashlib
import tempfile
from pathlib import Path

from ytforge.application.dto.editing import EditingRequest, EditingResult
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
_TARGET_RESOLUTION = "1920:1080"


class FFmpegRenderError(RuntimeError):
    pass


async def _run_ffmpeg(args: list[str]) -> None:
    process = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await process.communicate()
    if process.returncode != 0:
        raise FFmpegRenderError(f"ffmpeg exited {process.returncode}: {stderr.decode(errors='replace')[-2000:]}")


class FFmpegEditingPipeline:
    """Real FFmpeg-based renderer (ARCHITECTURE.md §5.1's "renderer queue"
    stage): pulls each scene's visual + voiceover bytes from object
    storage, renders one clip per scene (image scenes get a static-image-
    to-video treatment; clip scenes are re-encoded to a common codec/
    resolution so the concat demuxer can stitch them), concatenates, mixes
    in background music if present, and uploads the final render.

    # verify against a real ffmpeg install — no ffmpeg binary is available
    # in this dev sandbox, so this is built to the same honest-approximation
    # standard as Phase 6's under-documented provider adapters: exercised
    # here via unit tests that mock the subprocess call, not a real render.
    """

    def __init__(self, storage: ObjectStorage, raw_assets_bucket: str, renders_bucket: str) -> None:
        self._storage = storage
        self._raw_bucket = raw_assets_bucket
        self._renders_bucket = renders_bucket

    async def render(self, req: EditingRequest) -> EditingResult:
        async with record_provider_call("ffmpeg", "editing.render"):
            with tempfile.TemporaryDirectory(prefix="ytforge-render-") as tmpdir_raw:
                tmpdir = Path(tmpdir_raw)
                clip_paths = await self._render_scenes(req, tmpdir)
                concatenated = await self._concat_clips(clip_paths, tmpdir)
                final_path = await self._mix_music(req, concatenated, tmpdir)

                final_bytes = final_path.read_bytes()
                digest = hashlib.sha256(final_bytes).hexdigest()[:16]
                key = f"{req.project_id}/{digest}.mp4"
                await self._storage.put_object(self._renders_bucket, key, final_bytes, "video/mp4")

                total_duration = sum(scene.duration_seconds for scene in req.scenes)
                return EditingResult(render_object_key=key, duration_seconds=total_duration)

    async def _render_scenes(self, req: EditingRequest, tmpdir: Path) -> list[Path]:
        clip_paths: list[Path] = []
        for scene in sorted(req.scenes, key=lambda s: s.sequence_index):
            visual_bytes = await self._storage.get_object(self._raw_bucket, scene.visual_object_key)
            visual_path = tmpdir / f"visual_{scene.sequence_index}{Path(scene.visual_object_key).suffix}"
            visual_path.write_bytes(visual_bytes)

            voice_path: Path | None = None
            if scene.voice_object_key:
                voice_bytes = await self._storage.get_object(self._raw_bucket, scene.voice_object_key)
                voice_path = tmpdir / f"voice_{scene.sequence_index}{Path(scene.voice_object_key).suffix}"
                voice_path.write_bytes(voice_bytes)

            out_path = tmpdir / f"scene_{scene.sequence_index}.mp4"
            await self._render_scene(visual_path, voice_path, scene.duration_seconds, out_path)
            clip_paths.append(out_path)
        return clip_paths

    async def _render_scene(
        self, visual_path: Path, voice_path: Path | None, duration_seconds: float, out_path: Path
    ) -> None:
        is_image = visual_path.suffix.lower() in _IMAGE_SUFFIXES
        args: list[str] = []
        if is_image:
            args += ["-loop", "1", "-i", str(visual_path)]
        else:
            args += ["-i", str(visual_path)]
        if voice_path is not None:
            args += ["-i", str(voice_path)]
        else:
            args += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
        args += [
            "-t", str(duration_seconds),
            "-vf", f"scale={_TARGET_RESOLUTION}",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(out_path),
        ]
        await _run_ffmpeg(args)

    async def _concat_clips(self, clip_paths: list[Path], tmpdir: Path) -> Path:
        list_path = tmpdir / "concat_list.txt"
        list_path.write_text("".join(f"file '{p.as_posix()}'\n" for p in clip_paths), encoding="utf-8")
        out_path = tmpdir / "concatenated.mp4"
        await _run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(list_path), "-c", "copy", str(out_path)])
        return out_path

    async def _mix_music(self, req: EditingRequest, concatenated: Path, tmpdir: Path) -> Path:
        if not req.music_object_key:
            return concatenated
        music_bytes = await self._storage.get_object(self._raw_bucket, req.music_object_key)
        music_path = tmpdir / f"music{Path(req.music_object_key).suffix}"
        music_path.write_bytes(music_bytes)
        out_path = tmpdir / "final.mp4"
        await _run_ffmpeg(
            [
                "-i", str(concatenated),
                "-i", str(music_path),
                "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2[a]",
                "-map", "0:v",
                "-map", "[a]",
                "-c:v", "copy",
                str(out_path),
            ]
        )
        return out_path
