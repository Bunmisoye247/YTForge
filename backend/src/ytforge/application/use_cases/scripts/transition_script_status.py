from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ytforge.application.common.errors import InvalidStateError, NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Script
from ytforge.domain.enums import ScriptStatus
from ytforge.domain.errors import InvalidTransitionError


async def transition_script_status(
    uow: UnitOfWork, script_id: uuid.UUID, status: ScriptStatus
) -> Script:
    script = await uow.scripts.get_by_id(script_id)
    if script is None:
        raise NotFoundError("Script", script_id)

    from_status = script.status
    try:
        script.transition_to(status)
    except InvalidTransitionError as exc:
        raise InvalidStateError(exc) from exc
    script.updated_at = datetime.now(UTC)

    await uow.scripts.update(script)
    await uow.add_event(
        aggregate_type="script",
        aggregate_id=script.id,
        event_type="ScriptStatusChanged",
        payload={"from_status": from_status.value, "to_status": status.value},
    )
    await uow.commit()
    return script
