from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ytforge.application.common.errors import ConflictError, NotFoundError
from ytforge.application.common.pagination import PageParams
from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.use_cases.seo import (
    SetSeoMetadataInput,
    get_seo_metadata,
    set_seo_metadata,
)
from ytforge.application.use_cases.videos import (
    CreateVideoInput,
    UpdateVideoInput,
    create_video,
    list_videos,
    request_publish_approval,
    update_video,
)
from ytforge.domain.enums import ChannelRole
from ytforge.interfaces.api.deps.auth import CurrentUser, require_project_role
from ytforge.interfaces.api.deps.db import get_uow
from ytforge.interfaces.api.deps.pagination import page_params
from ytforge.interfaces.api.schemas.approvals import ApprovalRead
from ytforge.interfaces.api.schemas.pagination import PageResponse
from ytforge.interfaces.api.schemas.videos import (
    SeoMetadataRead,
    SeoMetadataSetRequest,
    VideoCreateRequest,
    VideoRead,
    VideoUpdateRequest,
)

router = APIRouter(tags=["videos"])


@router.post(
    "/projects/{project_id}/videos", response_model=VideoRead, status_code=status.HTTP_201_CREATED
)
async def create(
    project_id: uuid.UUID,
    data: VideoCreateRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _actor: Annotated[object, Depends(require_project_role(ChannelRole.EDITOR))],
) -> VideoRead:
    try:
        video = await create_video(
            uow,
            CreateVideoInput(
                project_id=project_id,
                render_asset_id=data.render_asset_id,
                title=data.title,
                description=data.description,
                synthetic_content_disclosure=data.synthetic_content_disclosure,
            ),
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return VideoRead.model_validate(video)


@router.get("/projects/{project_id}/videos", response_model=PageResponse[VideoRead])
async def list_(
    project_id: uuid.UUID,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    params: Annotated[PageParams, Depends(page_params)],
    _actor: Annotated[object, Depends(require_project_role(ChannelRole.VIEWER))],
) -> PageResponse[VideoRead]:
    page = await list_videos(uow, project_id, params)
    return PageResponse.from_page(page, VideoRead)


@router.patch("/videos/{video_id}", response_model=VideoRead)
async def update(
    video_id: uuid.UUID,
    data: VideoUpdateRequest,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> VideoRead:
    try:
        video = await update_video(
            uow, video_id, UpdateVideoInput(title=data.title, description=data.description)
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return VideoRead.model_validate(video)


@router.post(
    "/videos/{video_id}/request-publish-approval",
    response_model=ApprovalRead,
    status_code=status.HTTP_201_CREATED,
)
async def request_publish(
    video_id: uuid.UUID, user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> ApprovalRead:
    """The actual YouTube upload (and the video's DRAFT -> UPLOADED
    transition) is Phase-8 code triggered once this approval is granted."""
    try:
        approval = await request_publish_approval(uow, video_id, user.id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return ApprovalRead.model_validate(approval)


@router.get("/videos/{video_id}/seo", response_model=SeoMetadataRead)
async def get_seo(
    video_id: uuid.UUID, user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> SeoMetadataRead:
    try:
        seo = await get_seo_metadata(uow, video_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return SeoMetadataRead.model_validate(seo)


@router.put("/videos/{video_id}/seo", response_model=SeoMetadataRead)
async def set_seo(
    video_id: uuid.UUID,
    data: SeoMetadataSetRequest,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> SeoMetadataRead:
    try:
        seo = await set_seo_metadata(
            uow,
            SetSeoMetadataInput(
                video_id=video_id,
                title=data.title,
                description=data.description,
                thumbnail_asset_id=data.thumbnail_asset_id,
                tags=data.tags,
                chapters=data.chapters,
                keywords=data.keywords,
            ),
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return SeoMetadataRead.model_validate(seo)
