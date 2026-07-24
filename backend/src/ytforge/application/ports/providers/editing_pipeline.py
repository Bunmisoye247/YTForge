from __future__ import annotations

from typing import Protocol

from ytforge.application.dto.editing import EditingRequest, EditingResult


class EditingPipeline(Protocol):
    """Real implementation (FFmpeg pipeline, silence trimmer, caption
    burner per ARCHITECTURE.md §5.1) lands with the renderer worker.
    Phase 6's `EditingAgent` is built against this port now."""

    async def render(self, req: EditingRequest) -> EditingResult: ...
