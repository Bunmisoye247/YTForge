from __future__ import annotations

from datetime import UTC, datetime

import pytest
from uuid6 import uuid7

from ytforge.domain.entities import Storyboard
from ytforge.domain.enums import StoryboardStatus
from ytforge.domain.errors import InvalidTransitionError


def _make_storyboard(status: StoryboardStatus = StoryboardStatus.DRAFT) -> Storyboard:
    now = datetime.now(UTC)
    return Storyboard(
        id=uuid7(), project_id=uuid7(), script_id=uuid7(), status=status, created_at=now, updated_at=now
    )


def test_draft_to_ready() -> None:
    storyboard = _make_storyboard(StoryboardStatus.DRAFT)
    storyboard.transition_to(StoryboardStatus.READY)
    assert storyboard.status == StoryboardStatus.READY


def test_ready_to_approved() -> None:
    storyboard = _make_storyboard(StoryboardStatus.READY)
    storyboard.transition_to(StoryboardStatus.APPROVED)
    assert storyboard.status == StoryboardStatus.APPROVED


def test_approved_is_terminal() -> None:
    storyboard = _make_storyboard(StoryboardStatus.APPROVED)
    with pytest.raises(InvalidTransitionError):
        storyboard.transition_to(StoryboardStatus.READY)
