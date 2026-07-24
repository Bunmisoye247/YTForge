from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from ytforge.application.common.pagination import PageParams
from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.use_cases.trends import RecordTrendInput, list_trends, record_trend
from ytforge.domain.enums import ChannelRole
from ytforge.interfaces.api.deps.auth import require_channel_role
from ytforge.interfaces.api.deps.db import get_uow
from ytforge.interfaces.api.deps.pagination import page_params
from ytforge.interfaces.api.schemas.pagination import PageResponse
from ytforge.interfaces.api.schemas.trends import TrendCreateRequest, TrendRead

router = APIRouter(prefix="/channels/{channel_id}/trends", tags=["trends"])


@router.post("", response_model=TrendRead, status_code=status.HTTP_201_CREATED)
async def record(
    channel_id: uuid.UUID,
    data: TrendCreateRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _actor: Annotated[object, Depends(require_channel_role(ChannelRole.EDITOR))],
) -> TrendRead:
    trend = await record_trend(
        uow,
        RecordTrendInput(
            channel_id=channel_id,
            source=data.source,
            topic=data.topic,
            url=data.url,
            score=data.score,
            raw_payload=data.raw_payload,
        ),
    )
    return TrendRead.model_validate(trend)


@router.get("", response_model=PageResponse[TrendRead])
async def list_(
    channel_id: uuid.UUID,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    params: Annotated[PageParams, Depends(page_params)],
    _actor: Annotated[object, Depends(require_channel_role(ChannelRole.VIEWER))],
) -> PageResponse[TrendRead]:
    page = await list_trends(uow, channel_id, params)
    return PageResponse.from_page(page, TrendRead)
