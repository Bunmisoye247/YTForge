from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ytforge.domain.enums import ChannelRole


@dataclass(slots=True, kw_only=True)
class Channel:
    id: uuid.UUID
    name: str
    youtube_channel_id: str | None
    created_at: datetime
    updated_at: datetime
    brand_kit: dict[str, Any] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=dict)
    # Plaintext in memory only — the repository encrypts/decrypts this at
    # the DB boundary (ARCHITECTURE.md §8 envelope encryption); domain and
    # application code never see the ciphertext.
    oauth_refresh_token: str | None = None


@dataclass(slots=True, kw_only=True)
class ChannelMember:
    id: uuid.UUID
    channel_id: uuid.UUID
    user_id: uuid.UUID
    role: ChannelRole
    created_at: datetime
    updated_at: datetime
