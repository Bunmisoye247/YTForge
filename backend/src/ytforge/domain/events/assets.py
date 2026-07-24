from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AssetOrphaned:
    asset_id: uuid.UUID
