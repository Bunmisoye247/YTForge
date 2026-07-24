from __future__ import annotations

import pytest
from uuid6 import uuid7

from ytforge.application.common.errors import AuthenticationError
from ytforge.infrastructure.security.oauth_state import sign_oauth_state, verify_oauth_state

_SECRET = "test-secret"


def test_sign_then_verify_round_trips_channel_id() -> None:
    channel_id = uuid7()

    state = sign_oauth_state(_SECRET, channel_id)

    assert verify_oauth_state(_SECRET, state) == channel_id


def test_verify_rejects_wrong_secret() -> None:
    state = sign_oauth_state(_SECRET, uuid7())

    with pytest.raises(AuthenticationError):
        verify_oauth_state("different-secret", state)


def test_verify_rejects_garbage_state() -> None:
    with pytest.raises(AuthenticationError):
        verify_oauth_state(_SECRET, "not-a-real-jwt")
