from __future__ import annotations

from datetime import UTC, datetime

import pytest
from uuid6 import uuid7

from ytforge.domain.entities import Script
from ytforge.domain.enums import ScriptStatus
from ytforge.domain.errors import InvalidTransitionError


def _make_script(status: ScriptStatus = ScriptStatus.DRAFT) -> Script:
    now = datetime.now(UTC)
    return Script(
        id=uuid7(), project_id=uuid7(), version=1, status=status, created_at=now, updated_at=now
    )


def test_draft_to_in_review() -> None:
    script = _make_script(ScriptStatus.DRAFT)
    script.transition_to(ScriptStatus.IN_REVIEW)
    assert script.status == ScriptStatus.IN_REVIEW


def test_draft_cannot_go_directly_to_approved() -> None:
    script = _make_script(ScriptStatus.DRAFT)
    with pytest.raises(InvalidTransitionError):
        script.transition_to(ScriptStatus.APPROVED)


def test_approved_is_terminal() -> None:
    script = _make_script(ScriptStatus.APPROVED)
    with pytest.raises(InvalidTransitionError):
        script.transition_to(ScriptStatus.IN_REVIEW)


def test_rejected_can_be_redrafted() -> None:
    script = _make_script(ScriptStatus.REJECTED)
    script.transition_to(ScriptStatus.DRAFT)
    assert script.status == ScriptStatus.DRAFT
