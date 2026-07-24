from __future__ import annotations

from datetime import UTC, datetime

import pytest
from uuid6 import uuid7

from ytforge.domain.entities import VoiceProfile
from ytforge.domain.enums import VoiceProfileStatus
from ytforge.domain.errors import InvalidTransitionError


def _make_profile(status: VoiceProfileStatus = VoiceProfileStatus.PENDING_APPROVAL) -> VoiceProfile:
    now = datetime.now(UTC)
    return VoiceProfile(
        id=uuid7(),
        channel_id=uuid7(),
        name="Narrator",
        provider="elevenlabs",
        provider_voice_id="voice-1",
        status=status,
        consent_artifact_object_key="channel/consent.pdf",
        consent_recorded_at=now,
        created_at=now,
        updated_at=now,
    )


def test_pending_approval_to_approved() -> None:
    profile = _make_profile(VoiceProfileStatus.PENDING_APPROVAL)
    profile.approve()
    assert profile.status == VoiceProfileStatus.APPROVED


def test_approved_to_revoked() -> None:
    profile = _make_profile(VoiceProfileStatus.APPROVED)
    profile.revoke()
    assert profile.status == VoiceProfileStatus.REVOKED


def test_revoked_is_terminal() -> None:
    profile = _make_profile(VoiceProfileStatus.REVOKED)
    with pytest.raises(InvalidTransitionError):
        profile.approve()
