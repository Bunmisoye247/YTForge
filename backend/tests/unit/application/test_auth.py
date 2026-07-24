from __future__ import annotations

import pytest

from fixtures.fakes import FakePasswordHasher, FakeTokenService, FakeUnitOfWork
from ytforge.application.common.errors import AuthenticationError, ConflictError
from ytforge.application.use_cases.auth import (
    AuthenticateUserInput,
    RegisterUserInput,
    authenticate_user,
    logout_all_sessions,
    refresh_session,
    register_user,
)


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def hasher() -> FakePasswordHasher:
    return FakePasswordHasher()


@pytest.fixture
def tokens() -> FakeTokenService:
    return FakeTokenService()


async def test_register_user_succeeds(uow: FakeUnitOfWork, hasher: FakePasswordHasher) -> None:
    user = await register_user(
        uow, hasher, RegisterUserInput(email="a@example.com", password="hunter22", full_name="A")
    )
    assert user.email == "a@example.com"
    assert uow.committed


async def test_register_user_duplicate_email_rejected(
    uow: FakeUnitOfWork, hasher: FakePasswordHasher
) -> None:
    data = RegisterUserInput(email="a@example.com", password="hunter22", full_name="A")
    await register_user(uow, hasher, data)
    with pytest.raises(ConflictError):
        await register_user(uow, hasher, data)


async def test_authenticate_user_success_issues_tokens(
    uow: FakeUnitOfWork, hasher: FakePasswordHasher, tokens: FakeTokenService
) -> None:
    await register_user(
        uow, hasher, RegisterUserInput(email="a@example.com", password="hunter22", full_name="A")
    )
    pair = await authenticate_user(
        uow, hasher, tokens, AuthenticateUserInput(email="a@example.com", password="hunter22")
    )
    assert pair.access_token
    assert pair.refresh_token


async def test_authenticate_user_wrong_password_rejected(
    uow: FakeUnitOfWork, hasher: FakePasswordHasher, tokens: FakeTokenService
) -> None:
    await register_user(
        uow, hasher, RegisterUserInput(email="a@example.com", password="hunter22", full_name="A")
    )
    with pytest.raises(AuthenticationError):
        await authenticate_user(
            uow, hasher, tokens, AuthenticateUserInput(email="a@example.com", password="wrong")
        )


async def test_refresh_session_rejects_superseded_token_version(
    uow: FakeUnitOfWork, hasher: FakePasswordHasher, tokens: FakeTokenService
) -> None:
    user = await register_user(
        uow, hasher, RegisterUserInput(email="a@example.com", password="hunter22", full_name="A")
    )
    old_refresh = tokens.issue_refresh_token(user.id, user.token_version)

    await logout_all_sessions(uow, user.id)

    with pytest.raises(AuthenticationError):
        await refresh_session(uow, tokens, old_refresh)
