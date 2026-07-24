from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from ytforge.application.common.pagination import Page, PageParams
from ytforge.infrastructure.db.base import Base


async def paginate[TOrm: Base, TDomain](
    session: AsyncSession,
    stmt: Select[tuple[TOrm]],
    params: PageParams,
    to_domain: Callable[[TOrm], TDomain],
) -> Page[TDomain]:
    """`stmt` should already carry its filters and ORDER BY; this just adds
    the count query and LIMIT/OFFSET."""
    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await session.scalars(stmt.limit(params.limit).offset(params.offset))
    items = [to_domain(row) for row in rows]
    return Page(items=items, total=total, limit=params.limit, offset=params.offset)
