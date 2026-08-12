from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ytforge.application.common.errors import InvalidStateError, NotFoundError
from ytforge.application.common.pagination import PageParams
from ytforge.application.dto.image import ImageRequest
from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.application.use_cases.assets import (
    RegisterAssetInput,
    list_assets,
    mark_asset_failed,
    mark_asset_ready,
    register_asset,
    request_asset_deletion,
)
from ytforge.domain.enums import AssetType, ChannelRole
from ytforge.infrastructure.config.settings import get_settings
from ytforge.infrastructure.providers.errors import AllProvidersExhaustedError
from ytforge.interfaces.agents.factory import build_agent_context
from ytforge.interfaces.api.deps.auth import CurrentUser, require_project_role
from ytforge.interfaces.api.deps.db import get_uow
from ytforge.interfaces.api.deps.pagination import page_params
from ytforge.interfaces.api.deps.storage import get_object_storage
from ytforge.interfaces.api.schemas.approvals import ApprovalRead
from ytforge.interfaces.api.schemas.assets import (
    AssetRead,
    AssetRegisterRequest,
    ImageGenerateRequest,
    PresignedUrlRead,
)
from ytforge.interfaces.api.schemas.pagination import PageResponse

router = APIRouter(tags=["assets"])


@router.post(
    "/projects/{project_id}/assets", response_model=AssetRead, status_code=status.HTTP_201_CREATED
)
async def register(
    project_id: uuid.UUID,
    data: AssetRegisterRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _actor: Annotated[object, Depends(require_project_role(ChannelRole.EDITOR))],
) -> AssetRead:
    try:
        asset = await register_asset(
            uow,
            RegisterAssetInput(
                project_id=project_id,
                asset_type=data.asset_type,
                bucket=data.bucket,
                object_key=data.object_key,
                scene_id=data.scene_id,
                checksum_sha256=data.checksum_sha256,
                provenance=data.provenance,
            ),
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return AssetRead.model_validate(asset)


@router.get("/projects/{project_id}/assets", response_model=PageResponse[AssetRead])
async def list_(
    project_id: uuid.UUID,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    params: Annotated[PageParams, Depends(page_params)],
    _actor: Annotated[object, Depends(require_project_role(ChannelRole.VIEWER))],
) -> PageResponse[AssetRead]:
    page = await list_assets(uow, project_id, params)
    return PageResponse.from_page(page, AssetRead)


@router.post(
    "/projects/{project_id}/assets/generate-image",
    response_model=list[AssetRead],
    status_code=status.HTTP_201_CREATED,
)
async def generate_image(
    project_id: uuid.UUID,
    data: ImageGenerateRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _actor: Annotated[object, Depends(require_project_role(ChannelRole.EDITOR))],
) -> list[AssetRead]:
    """Freeform prompt -> image, not tied to a storyboard scene (the
    Images page's "Create images" flow). Unlike
    storyboards.generate_image (which runs ImageAgent, including its
    script_writing prompt-refinement step derived from a scene's
    description), this calls ModelRouter directly with the operator's
    prompt exactly as typed — there's no scene to derive a prompt from."""
    settings = get_settings()
    ctx = build_agent_context(settings, uow)
    try:
        images = await ctx.model_router.generate_image(
            "image_generation",
            ImageRequest(
                prompt=data.prompt,
                model="",
                negative_prompt=data.negative_prompt,
                width=data.width,
                height=data.height,
            ),
        )
    except AllProvidersExhaustedError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    assets = []
    for image in images:
        asset = await register_asset(
            uow,
            RegisterAssetInput(
                project_id=project_id,
                asset_type=AssetType.IMAGE,
                bucket="raw-assets",
                object_key=image.object_key,
                provenance={"model": image.model, "cost_usd": image.cost_usd, "prompt": data.prompt},
            ),
        )
        await mark_asset_ready(uow, asset.id)
        assets.append(asset)
    return [AssetRead.model_validate(asset) for asset in assets]


@router.get("/assets/{asset_id}/presigned-url", response_model=PresignedUrlRead)
async def presigned_url(
    asset_id: uuid.UUID,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
) -> PresignedUrlRead:
    """A short-lived, browser-reachable URL for an asset's bytes
    (ARCHITECTURE.md §6.3: "All dashboard media access via presigned
    URLs — the API never proxies bytes")."""
    asset = await uow.assets.get_by_id(asset_id)
    if asset is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "asset not found")
    url = await storage.presigned_url(asset.bucket, asset.object_key)
    return PresignedUrlRead(url=url)


@router.post("/assets/{asset_id}/ready", response_model=AssetRead)
async def mark_ready(
    asset_id: uuid.UUID, user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> AssetRead:
    try:
        asset = await mark_asset_ready(uow, asset_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStateError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return AssetRead.model_validate(asset)


@router.post("/assets/{asset_id}/failed", response_model=AssetRead)
async def mark_failed(
    asset_id: uuid.UUID, user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> AssetRead:
    try:
        asset = await mark_asset_failed(uow, asset_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStateError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return AssetRead.model_validate(asset)


@router.post(
    "/assets/{asset_id}/request-deletion",
    response_model=ApprovalRead,
    status_code=status.HTTP_201_CREATED,
)
async def request_deletion(
    asset_id: uuid.UUID, user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> ApprovalRead:
    try:
        approval = await request_asset_deletion(uow, asset_id, user.id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return ApprovalRead.model_validate(approval)
