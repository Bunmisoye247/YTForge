from __future__ import annotations

from ytforge.application.common.errors import AuthenticationError
from ytforge.application.ports.providers import TokenService, UnitOfWork
from ytforge.application.use_cases.auth.authenticate_user import TokenPair


async def refresh_session(uow: UnitOfWork, tokens: TokenService, refresh_token: str) -> TokenPair:
    decoded = tokens.decode_refresh_token(refresh_token)
    user = await uow.users.get_by_id(decoded.user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("invalid refresh token")
    if user.token_version != decoded.token_version:
        raise AuthenticationError("refresh token has been superseded")

    return TokenPair(
        access_token=tokens.issue_access_token(user.id),
        refresh_token=tokens.issue_refresh_token(user.id, user.token_version),
        user=user,
    )
