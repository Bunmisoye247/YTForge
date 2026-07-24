from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.domain.entities import User
from ytforge.infrastructure.db.models import User as UserOrm


def _to_domain(row: UserOrm) -> User:
    return User(
        id=row.id,
        email=row.email,
        hashed_password=row.hashed_password,
        full_name=row.full_name,
        is_active=row.is_active,
        is_superuser=row.is_superuser,
        token_version=row.token_version,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        row = await self._session.get(UserOrm, user_id)
        return _to_domain(row) if row is not None else None

    async def get_by_email(self, email: str) -> User | None:
        row = await self._session.scalar(select(UserOrm).where(UserOrm.email == email))
        return _to_domain(row) if row is not None else None

    async def add(self, user: User) -> None:
        row = UserOrm(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            token_version=user.token_version,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def update(self, user: User) -> None:
        row = await self._session.get(UserOrm, user.id)
        assert row is not None
        row.email = user.email
        row.hashed_password = user.hashed_password
        row.full_name = user.full_name
        row.is_active = user.is_active
        row.is_superuser = user.is_superuser
        row.token_version = user.token_version
        row.updated_at = user.updated_at
        await self._session.flush()
