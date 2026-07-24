from __future__ import annotations

from datetime import UTC, datetime

import pytest
from uuid6 import uuid7

from ytforge.domain.entities import Approval
from ytforge.domain.enums import ApprovalKind, ApprovalStatus
from ytforge.domain.errors import InvalidTransitionError


def _make_approval(status: ApprovalStatus = ApprovalStatus.PENDING) -> Approval:
    now = datetime.now(UTC)
    return Approval(
        id=uuid7(), kind=ApprovalKind.PUBLISH, status=status, created_at=now, updated_at=now
    )


def test_pending_can_be_approved() -> None:
    approval = _make_approval(ApprovalStatus.PENDING)
    decider = uuid7()
    approval.decide(status=ApprovalStatus.APPROVED, decided_by_user_id=decider, decided_at=datetime.now(UTC))
    assert approval.status == ApprovalStatus.APPROVED
    assert approval.decided_by_user_id == decider


def test_pending_can_be_rejected() -> None:
    approval = _make_approval(ApprovalStatus.PENDING)
    approval.decide(
        status=ApprovalStatus.REJECTED, decided_by_user_id=uuid7(), decided_at=datetime.now(UTC), note="no"
    )
    assert approval.status == ApprovalStatus.REJECTED
    assert approval.note == "no"


def test_already_decided_cannot_be_decided_again() -> None:
    approval = _make_approval(ApprovalStatus.APPROVED)
    with pytest.raises(InvalidTransitionError):
        approval.decide(status=ApprovalStatus.REJECTED, decided_by_user_id=uuid7(), decided_at=datetime.now(UTC))


def test_cannot_decide_to_pending() -> None:
    approval = _make_approval(ApprovalStatus.PENDING)
    with pytest.raises(InvalidTransitionError):
        approval.decide(status=ApprovalStatus.PENDING, decided_by_user_id=uuid7(), decided_at=datetime.now(UTC))
