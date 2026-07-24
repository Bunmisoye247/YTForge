from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ytforge.application.common.errors import InvalidStateError, NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.use_cases.voice import (
    AddVoiceoverInput,
    RegisterVoiceProfileInput,
    RequestVoiceCloneInput,
    add_voiceover,
    approve_voice_profile,
    list_voice_profiles,
    list_voiceovers,
    register_voice_profile,
    request_voice_clone,
)
from ytforge.domain.enums import ChannelRole
from ytforge.interfaces.api.deps.auth import CurrentUser, require_channel_role, require_project_role
from ytforge.interfaces.api.deps.db import get_uow
from ytforge.interfaces.api.schemas.approvals import ApprovalRead
from ytforge.interfaces.api.schemas.voice import (
    VoiceCloneRequestRequest,
    VoiceoverCreateRequest,
    VoiceoverRead,
    VoiceProfileRead,
    VoiceProfileRegisterRequest,
)

router = APIRouter(tags=["voice"])


@router.post(
    "/channels/{channel_id}/voice-profiles/clone-requests",
    response_model=ApprovalRead,
    status_code=status.HTTP_201_CREATED,
)
async def request_clone(
    channel_id: uuid.UUID,
    data: VoiceCloneRequestRequest,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _actor: Annotated[object, Depends(require_channel_role(ChannelRole.ADMIN))],
) -> ApprovalRead:
    try:
        approval = await request_voice_clone(
            uow,
            RequestVoiceCloneInput(
                channel_id=channel_id,
                proposed_name=data.proposed_name,
                consent_artifact_object_key=data.consent_artifact_object_key,
                requested_by_user_id=user.id,
            ),
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return ApprovalRead.model_validate(approval)


@router.post(
    "/channels/{channel_id}/voice-profiles",
    response_model=VoiceProfileRead,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    channel_id: uuid.UUID,
    data: VoiceProfileRegisterRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _actor: Annotated[object, Depends(require_channel_role(ChannelRole.ADMIN))],
) -> VoiceProfileRead:
    try:
        profile = await register_voice_profile(
            uow,
            RegisterVoiceProfileInput(
                channel_id=channel_id,
                name=data.name,
                provider=data.provider,
                provider_voice_id=data.provider_voice_id,
                consent_artifact_object_key=data.consent_artifact_object_key,
                consent_recorded_at=data.consent_recorded_at,
            ),
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return VoiceProfileRead.model_validate(profile)


@router.get("/channels/{channel_id}/voice-profiles", response_model=list[VoiceProfileRead])
async def list_for_channel(
    channel_id: uuid.UUID,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> list[VoiceProfileRead]:
    profiles = await list_voice_profiles(uow, channel_id)
    return [VoiceProfileRead.model_validate(profile) for profile in profiles]


@router.post("/voice-profiles/{voice_profile_id}/approve", response_model=VoiceProfileRead)
async def approve(
    voice_profile_id: uuid.UUID, user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> VoiceProfileRead:
    try:
        profile = await approve_voice_profile(uow, voice_profile_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStateError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return VoiceProfileRead.model_validate(profile)


@router.post(
    "/projects/{project_id}/voiceovers", response_model=VoiceoverRead, status_code=status.HTTP_201_CREATED
)
async def add(
    project_id: uuid.UUID,
    data: VoiceoverCreateRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _actor: Annotated[object, Depends(require_project_role(ChannelRole.EDITOR))],
) -> VoiceoverRead:
    try:
        voiceover = await add_voiceover(
            uow,
            AddVoiceoverInput(
                project_id=project_id,
                asset_id=data.asset_id,
                transcript=data.transcript,
                duration_seconds=data.duration_seconds,
                scene_id=data.scene_id,
                voice_profile_id=data.voice_profile_id,
                word_timestamps=data.word_timestamps,
            ),
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return VoiceoverRead.model_validate(voiceover)


@router.get("/projects/{project_id}/voiceovers", response_model=list[VoiceoverRead])
async def list_for_project(
    project_id: uuid.UUID,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> list[VoiceoverRead]:
    voiceovers = await list_voiceovers(uow, project_id)
    return [VoiceoverRead.model_validate(voiceover) for voiceover in voiceovers]
