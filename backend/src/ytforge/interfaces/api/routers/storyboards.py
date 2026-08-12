from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ytforge.application.common.errors import ConflictError, InvalidStateError, NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.use_cases.storyboard import (
    AddSceneInput,
    add_scene,
    create_storyboard,
    get_storyboard_for_project,
    list_scenes,
    reorder_scenes,
    transition_storyboard_status,
)
from ytforge.domain.enums import ChannelRole
from ytforge.infrastructure.config.settings import get_settings
from ytforge.interfaces.agents import AGENTS, AgentTask
from ytforge.interfaces.agents.factory import build_agent_context
from ytforge.interfaces.api.deps.auth import CurrentUser, require_project_role
from ytforge.interfaces.api.deps.db import get_uow
from ytforge.interfaces.api.schemas.assets import AssetRead
from ytforge.interfaces.api.schemas.storyboards import (
    SceneCreateRequest,
    SceneRead,
    SceneReorderRequest,
    StoryboardCreateRequest,
    StoryboardRead,
    StoryboardStatusUpdateRequest,
)

router = APIRouter(tags=["storyboards"])


@router.post(
    "/projects/{project_id}/storyboards",
    response_model=StoryboardRead,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    project_id: uuid.UUID,
    data: StoryboardCreateRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _actor: Annotated[object, Depends(require_project_role(ChannelRole.EDITOR))],
) -> StoryboardRead:
    try:
        storyboard = await create_storyboard(uow, project_id, data.script_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return StoryboardRead.model_validate(storyboard)


@router.get("/projects/{project_id}/storyboard", response_model=StoryboardRead)
async def get_for_project(
    project_id: uuid.UUID,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> StoryboardRead:
    try:
        storyboard = await get_storyboard_for_project(uow, project_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return StoryboardRead.model_validate(storyboard)


@router.get("/storyboards/{storyboard_id}/scenes", response_model=list[SceneRead])
async def list_(
    storyboard_id: uuid.UUID,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> list[SceneRead]:
    scenes = await list_scenes(uow, storyboard_id)
    return [SceneRead.model_validate(scene) for scene in scenes]


@router.post("/storyboards/{storyboard_id}/status", response_model=StoryboardRead)
async def update_status(
    storyboard_id: uuid.UUID,
    data: StoryboardStatusUpdateRequest,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> StoryboardRead:
    try:
        storyboard = await transition_storyboard_status(uow, storyboard_id, data.status)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStateError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return StoryboardRead.model_validate(storyboard)


@router.post(
    "/storyboards/{storyboard_id}/scenes", response_model=SceneRead, status_code=status.HTTP_201_CREATED
)
async def add(
    storyboard_id: uuid.UUID,
    data: SceneCreateRequest,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> SceneRead:
    try:
        scene = await add_scene(
            uow,
            AddSceneInput(
                storyboard_id=storyboard_id,
                sequence_index=data.sequence_index,
                description=data.description,
                duration_seconds=data.duration_seconds,
                image_prompt=data.image_prompt,
                video_prompt=data.video_prompt,
                voice_line=data.voice_line,
            ),
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return SceneRead.model_validate(scene)


@router.post("/storyboards/{storyboard_id}/scenes/reorder", response_model=list[SceneRead])
async def reorder(
    storyboard_id: uuid.UUID,
    data: SceneReorderRequest,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> list[SceneRead]:
    try:
        scenes = await reorder_scenes(uow, storyboard_id, data.ordered_scene_ids)
    except (NotFoundError, ConflictError) as exc:
        code = status.HTTP_404_NOT_FOUND if isinstance(exc, NotFoundError) else status.HTTP_409_CONFLICT
        raise HTTPException(code, str(exc)) from exc
    return [SceneRead.model_validate(scene) for scene in scenes]


@router.post(
    "/projects/{project_id}/scenes/{scene_id}/generate-image",
    response_model=list[AssetRead],
    status_code=status.HTTP_201_CREATED,
)
async def generate_image(
    project_id: uuid.UUID,
    scene_id: uuid.UUID,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _actor: Annotated[object, Depends(require_project_role(ChannelRole.EDITOR))],
) -> list[AssetRead]:
    """Runs ImageAgent for a single scene outside the full
    VideoProductionWorkflow — the same agent, context, and provider
    routing (ModelRouter's image_generation route, Pollinations/ComfyUI/
    A1111/Flux per config/default.yaml) the pipeline uses, just invoked
    directly and synchronously (same reuse pattern as the `run-agent` CLI
    command) so a single image can be generated or regenerated without
    running the whole workflow."""
    settings = get_settings()
    ctx = build_agent_context(settings, uow)
    task = AgentTask(project_id=project_id, payload={"scene_ids": [str(scene_id)]})
    result = await AGENTS["image"].run(task, ctx)
    if not result.ok:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, result.error or "image generation failed")

    asset_ids = result.output.get("asset_ids", [])
    assets = []
    for asset_id_raw in asset_ids:
        asset = await uow.assets.get_by_id(uuid.UUID(asset_id_raw))
        if asset is not None:
            assets.append(asset)
    return [AssetRead.model_validate(asset) for asset in assets]
