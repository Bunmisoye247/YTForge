from __future__ import annotations

from collections.abc import AsyncIterator

from ytforge.infrastructure.db.session import get_session_factory
from ytforge.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork


async def get_uow() -> AsyncIterator[SqlAlchemyUnitOfWork]:
    uow = SqlAlchemyUnitOfWork(get_session_factory())
    async with uow:
        yield uow
