from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork


@dataclass(frozen=True, slots=True)
class BudgetStatus:
    spent_usd: Decimal
    budget_usd: Decimal | None
    remaining_usd: Decimal | None

    @property
    def is_exhausted(self) -> bool:
        return self.remaining_usd is not None and self.remaining_usd <= 0


async def check_budget(uow: UnitOfWork, project_id: uuid.UUID) -> BudgetStatus:
    """Sums `prompt_runs.cost_usd` for the project against `Project.budget_usd`.
    Per ARCHITECTURE.md §5.1's "budget guard" — callers (agents) check this
    before an expensive provider call and should route to a review gate
    instead of proceeding when `is_exhausted` is true. A project with no
    `budget_usd` set is treated as unbounded (`remaining_usd` is None)."""
    project = await uow.projects.get_by_id(project_id)
    if project is None:
        raise NotFoundError("Project", project_id)

    spent = await uow.prompt_runs.sum_cost_for_project(project_id)
    if project.budget_usd is None:
        return BudgetStatus(spent_usd=spent, budget_usd=None, remaining_usd=None)

    return BudgetStatus(
        spent_usd=spent,
        budget_usd=project.budget_usd,
        remaining_usd=project.budget_usd - spent,
    )
