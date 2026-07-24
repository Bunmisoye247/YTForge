from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VoiceProfileApproved:
    voice_profile_id: uuid.UUID
