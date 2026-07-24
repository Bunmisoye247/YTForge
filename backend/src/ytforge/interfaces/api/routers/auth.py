from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from ytforge.application.common.errors import AuthenticationError, ConflictError, NotFoundError
from ytforge.application.ports.providers import PasswordHasher, TokenService, UnitOfWork
from ytforge.application.use_cases.auth import (
    AuthenticateUserInput,
    RegisterUserInput,
    authenticate_user,
    logout_all_sessions,
    refresh_session,
    register_user,
)
from ytforge.application.use_cases.channels import LinkYouTubeChannelInput, link_youtube_channel
from ytforge.infrastructure.config.settings import get_settings
from ytforge.infrastructure.external.google.oauth_client import GoogleOAuthClient
from ytforge.infrastructure.security.oauth_state import sign_oauth_state, verify_oauth_state
from ytforge.interfaces.api.deps.auth import CurrentUser
from ytforge.interfaces.api.deps.db import get_uow
from ytforge.interfaces.api.deps.security import get_password_hasher, get_token_service
from ytforge.interfaces.api.schemas.auth import AccessTokenResponse, RegisterRequest, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE_NAME = "refresh_token"
_REFRESH_COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=_REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.app.env != "development",
        samesite="lax",
        path=_REFRESH_COOKIE_PATH,
        max_age=settings.security.refresh_token_ttl_days * 24 * 60 * 60,
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
) -> UserRead:
    try:
        user = await register_user(
            uow, hasher, RegisterUserInput(email=data.email, password=data.password, full_name=data.full_name)
        )
    except ConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return UserRead.model_validate(user)


@router.post("/login", response_model=AccessTokenResponse)
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    tokens: Annotated[TokenService, Depends(get_token_service)],
) -> AccessTokenResponse:
    try:
        pair = await authenticate_user(
            uow, hasher, tokens, AuthenticateUserInput(email=form_data.username, password=form_data.password)
        )
    except AuthenticationError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    _set_refresh_cookie(response, pair.refresh_token)
    return AccessTokenResponse(access_token=pair.access_token, user=UserRead.model_validate(pair.user))


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    response: Response,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    tokens: Annotated[TokenService, Depends(get_token_service)],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> AccessTokenResponse:
    if refresh_token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing refresh token")
    try:
        pair = await refresh_session(uow, tokens, refresh_token)
    except AuthenticationError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    _set_refresh_cookie(response, pair.refresh_token)
    return AccessTokenResponse(access_token=pair.access_token, user=UserRead.model_validate(pair.user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> None:
    await logout_all_sessions(uow, user.id)
    response.delete_cookie(_REFRESH_COOKIE_NAME, path=_REFRESH_COOKIE_PATH)


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


def _google_oauth_client() -> GoogleOAuthClient:
    settings = get_settings().google_oauth
    return GoogleOAuthClient(settings.client_id, settings.client_secret.get_secret_value(), settings.redirect_uri)


@router.get("/google/authorize")
async def google_authorize(channel_id: uuid.UUID, user: CurrentUser) -> RedirectResponse:
    """Starts the Google OAuth flow to link `channel_id`'s YouTube account
    (ARCHITECTURE.md §7.1). Requires the caller to already be authenticated
    — `channel_id` is embedded in the signed `state` param so the callback
    (which Google redirects to with no auth headers of ours) knows which
    channel to link without a server-side session."""
    settings = get_settings()
    state = sign_oauth_state(settings.security.jwt_secret.get_secret_value(), channel_id)
    return RedirectResponse(_google_oauth_client().build_authorize_url(state))


@router.get("/google/callback")
async def google_callback(
    code: str, state: str, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> dict[str, str]:
    settings = get_settings()
    try:
        channel_id = verify_oauth_state(settings.security.jwt_secret.get_secret_value(), state)
    except AuthenticationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    oauth_client = _google_oauth_client()
    tokens = await oauth_client.exchange_code(code)
    if tokens.refresh_token is None:
        # Google only returns a refresh token on the FIRST consent for a
        # given client+account (or when access_type=offline&prompt=consent
        # forces re-consent, which build_authorize_url always sets) — this
        # branch means Google's behavior deviated from that, not a bug here.
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Google did not return a refresh token")
    youtube_channel_id = await oauth_client.fetch_my_channel_id(tokens.access_token)

    try:
        await link_youtube_channel(
            uow, channel_id, LinkYouTubeChannelInput(youtube_channel_id=youtube_channel_id, refresh_token=tokens.refresh_token)
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    return {"status": "linked", "youtube_channel_id": youtube_channel_id}
