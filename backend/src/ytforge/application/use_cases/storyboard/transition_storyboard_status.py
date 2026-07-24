from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ytforge.application.common.errors import InvalidStateError, NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Storyboard
from ytforge.domain.enums import StoryboardStatus
from ytforge.domain.errors import InvalidTransitionError


async def transition_storyboard_status(
    uow: UnitOfWork, storyboard_id: uuid.UUID, status: StoryboardStatus
) -> Storyboard:
    storyboard = await uow.storyboards.get_by_id(storyboard_id)
    if storyboard is None:
        raise NotFoundError("Storyboard", storyboard_id)

    try:
        storyboard.transition_to(status)
    except InvalidTransitionError as exc:
        raise InvalidStateError(exc) from exc
    storyboard.updated_at = datetime.now(UTC)

    await uow.storyboards.update(storyboard)
    await uow.commit()
    return storyboard
