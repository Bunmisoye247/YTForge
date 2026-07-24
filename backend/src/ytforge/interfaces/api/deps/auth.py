from __future__ import annotations

import uuid
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ytforge.application.common.errors import AuthenticationError, NotFoundError
from ytforge.application.ports.providers import TokenService, UnitOfWork
from ytforge.domain.entities import User
from ytforge.domain.enums import ChannelRole
from ytforge.infrastructure.security.rbac import resolve_channel_role, role_satisfies
from ytforge.interfaces.api.deps.db import get_uow
from ytforge.interfaces.api.deps.security import get_token_service

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: Annotated[str | None, Depends(_oauth2_scheme)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    tokens: Annotated[TokenService, Depends(get_token_service)],
) -> User:
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")

    try:
        decoded = tokens.decode_access_token(token)
    except AuthenticationError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    user = await uow.users.get_by_id(decoded.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_channel_role(
    minimum: ChannelRole,
) -> Callable[..., Coroutine[Any, Any, User]]:
    async def dependency(
        channel_id: uuid.UUID,
        user: CurrentUser,
        uow: Annotated[UnitOfWork, Depends(get_uow)],
    ) -> User:
        if user.is_superuser:
            return user
        role = await resolve_channel_role(uow, user.id, channel_id)
        if role is None or not role_satisfies(role, minimum):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "insufficient channel role")
        return user

    return dependency


def require_project_role(
    minimum: ChannelRole,
) -> Callable[..., Coroutine[Any, Any, User]]:
    """For routes scoped by `project_id` rather than `channel_id` directly —
    resolves the project's owning channel, then checks the role there."""

    async def dependency(
        project_id: uuid.UUID,
        user: CurrentUser,
        uow: Annotated[UnitOfWork, Depends(get_uow)],
    ) -> User:
        if user.is_superuser:
            return user
        project = await uow.projects.get_by_id(project_id)
        if project is None:
            raise NotFoundError("Project", project_id)
        role = await resolve_channel_role(uow, user.id, project.channel_id)
        if role is None or not role_satisfies(role, minimum):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "insufficient channel role")
        return user

    return dependency
