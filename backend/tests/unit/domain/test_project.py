from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from uuid6 import uuid7

from ytforge.domain.entities import Project
from ytforge.domain.enums import ProjectStatus
from ytforge.domain.errors import InvalidTransitionError


def _make_project(status: ProjectStatus = ProjectStatus.IDEA) -> Project:
    now = datetime.now(UTC)
    return Project(
        id=uuid7(),
        channel_id=uuid7(),
        trend_id=None,
        created_by_user_id=None,
        title="Test project",
        status=status,
        budget_usd=Decimal("100.00"),
        created_at=now,
        updated_at=now,
    )


def test_idea_can_transition_to_in_progress() -> None:
    project = _make_project(ProjectStatus.IDEA)
    project.transition_to(ProjectStatus.IN_PROGRESS)
    assert project.status == ProjectStatus.IN_PROGRESS


def test_idea_cannot_transition_to_completed() -> None:
    project = _make_project(ProjectStatus.IDEA)
    with pytest.raises(InvalidTransitionError):
        project.transition_to(ProjectStatus.COMPLETED)


def test_archived_is_terminal() -> None:
    project = _make_project(ProjectStatus.ARCHIVED)
    with pytest.raises(InvalidTransitionError):
        project.transition_to(ProjectStatus.IN_PROGRESS)
