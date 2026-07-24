from __future__ import annotations

import hashlib

from ytforge.application.dto.editing import EditingRequest, EditingResult


class FakeEditingPipeline:
    """Deterministic stand-in for `FFmpegEditingPipeline` — no ffmpeg
    binary needed, matches the fakeprovider set's role for e2e agent tests
    (`YTFORGE__MODELS__PROVIDER_SET=fake`)."""

    async def render(self, req: EditingRequest) -> EditingResult:
        digest = hashlib.sha256(req.project_id.encode()).hexdigest()[:16]
        total_duration = sum(scene.duration_seconds for scene in req.scenes)
        return EditingResult(render_object_key=f"{req.project_id}/{digest}.mp4", duration_seconds=total_duration)
