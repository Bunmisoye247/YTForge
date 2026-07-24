from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ytforge.application.common.errors import ConflictError, NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Scene


async def reorder_scenes(
    uow: UnitOfWork, storyboard_id: uuid.UUID, ordered_scene_ids: list[uuid.UUID]
) -> list[Scene]:
    scenes = await uow.scenes.list_for_storyboard(storyboard_id)
    scenes_by_id = {scene.id: scene for scene in scenes}
    if set(scenes_by_id) != set(ordered_scene_ids):
        raise ConflictError("ordered_scene_ids must contain exactly the storyboard's scenes")

    now = datetime.now(UTC)
    # Two-pass update: the unique (storyboard_id, sequence_index) constraint
    # would collide mid-flush if swapped indexes were written directly, so
    # every scene is first pushed past the current index range and only then
    # assigned its final position.
    offset = len(scenes)
    for scene in scenes_by_id.values():
        scene.sequence_index += offset
        scene.updated_at = now
        await uow.scenes.update(scene)

    updated: list[Scene] = []
    for index, scene_id in enumerate(ordered_scene_ids):
        target = scenes_by_id.get(scene_id)
        if target is None:
            raise NotFoundError("Scene", scene_id)
        target.sequence_index = index
        target.updated_at = now
        await uow.scenes.update(target)
        updated.append(target)

    await uow.commit()
    return updated
