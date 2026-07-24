from __future__ import annotations

from dataclasses import dataclass

from ytforge.application.common.errors import AuthenticationError
from ytforge.application.ports.providers import PasswordHasher, TokenService, UnitOfWork
from ytforge.domain.entities import User


@dataclass(frozen=True, slots=True)
class AuthenticateUserInput:
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    user: User


_INVALID_CREDENTIALS = "invalid email or password"


async def authenticate_user(
    uow: UnitOfWork,
    hasher: PasswordHasher,
    tokens: TokenService,
    data: AuthenticateUserInput,
) -> TokenPair:
    user = await uow.users.get_by_email(data.email)
    if user is None or not hasher.verify(data.password, user.hashed_password):
        raise AuthenticationError(_INVALID_CREDENTIALS)
    if not user.is_active:
        raise AuthenticationError("this account has been deactivated")

    return TokenPair(
        access_token=tokens.issue_access_token(user.id),
        refresh_token=tokens.issue_refresh_token(user.id, user.token_version),
        user=user,
    )
