from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ytforge.domain.enums import AssetStatus, AssetType
from ytforge.domain.errors import InvalidTransitionError

_LEGAL_TRANSITIONS: dict[AssetStatus, frozenset[AssetStatus]] = {
    AssetStatus.PENDING: frozenset({AssetStatus.READY, AssetStatus.FAILED}),
    AssetStatus.READY: frozenset({AssetStatus.ORPHANED}),
    AssetStatus.FAILED: frozenset({AssetStatus.PENDING}),
    AssetStatus.ORPHANED: frozenset(),
}


@dataclass(slots=True, kw_only=True)
class Asset:
    id: uuid.UUID
    project_id: uuid.UUID
    scene_id: uuid.UUID | None
    asset_type: AssetType
    status: AssetStatus
    bucket: str
    object_key: str
    created_at: datetime
    updated_at: datetime
    checksum_sha256: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def mark_ready(self) -> None:
        self._transition(AssetStatus.READY)

    def mark_failed(self) -> None:
        self._transition(AssetStatus.FAILED)

    def orphan(self) -> None:
        """Soft delete. Only called after the ASSET_DELETION approval is granted."""
        self._transition(AssetStatus.ORPHANED)

    def _transition(self, status: AssetStatus) -> None:
        if status not in _LEGAL_TRANSITIONS[self.status]:
            raise InvalidTransitionError("Asset", self.status.value, status.value)
        self.status = status
