from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork


async def logout_all_sessions(uow: UnitOfWork, user_id: uuid.UUID) -> None:
    user = await uow.users.get_by_id(user_id)
    if user is None:
        raise NotFoundError("User", user_id)
    user.token_version += 1
    user.updated_at = datetime.now(UTC)
    await uow.users.update(user)
    await uow.commit()
