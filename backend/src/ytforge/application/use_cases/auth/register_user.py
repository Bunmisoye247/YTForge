from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from uuid6 import uuid7

from ytforge.application.common.errors import ConflictError
from ytforge.application.ports.providers import PasswordHasher, UnitOfWork
from ytforge.domain.entities import User


@dataclass(frozen=True, slots=True)
class RegisterUserInput:
    email: str
    password: str
    full_name: str


async def register_user(
    uow: UnitOfWork, hasher: PasswordHasher, data: RegisterUserInput
) -> User:
    if await uow.users.get_by_email(data.email) is not None:
        raise ConflictError(f"a user with email {data.email!r} already exists")

    now = datetime.now(UTC)
    user = User(
        id=uuid7(),
        email=data.email,
        hashed_password=hasher.hash(data.password),
        full_name=data.full_name,
        is_active=True,
        is_superuser=False,
        token_version=0,
        created_at=now,
        updated_at=now,
    )
    await uow.users.add(user)
    await uow.commit()
    return user
