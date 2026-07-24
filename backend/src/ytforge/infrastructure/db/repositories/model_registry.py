from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.domain.entities import ModelRegistryEntry
from ytforge.infrastructure.db.models import ModelRegistryEntry as ModelRegistryEntryOrm


def _to_domain(row: ModelRegistryEntryOrm) -> ModelRegistryEntry:
    return ModelRegistryEntry(
        id=row.id,
        provider=row.provider,
        model_name=row.model_name,
        capability=row.capability,
        status=row.status,
        discovered_at=row.discovered_at,
        base_url=row.base_url,
        last_checked_at=row.last_checked_at,
        entry_metadata=row.entry_metadata,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyModelRegistryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entry_id: uuid.UUID) -> ModelRegistryEntry | None:
        row = await self._session.get(ModelRegistryEntryOrm, entry_id)
        return _to_domain(row) if row is not None else None

    async def add(self, entry: ModelRegistryEntry) -> None:
        row = ModelRegistryEntryOrm(
            id=entry.id,
            provider=entry.provider,
            model_name=entry.model_name,
            capability=entry.capability,
            base_url=entry.base_url,
            status=entry.status,
            discovered_at=entry.discovered_at,
            last_checked_at=entry.last_checked_at,
            entry_metadata=entry.entry_metadata,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def update(self, entry: ModelRegistryEntry) -> None:
        row = await self._session.get(ModelRegistryEntryOrm, entry.id)
        assert row is not None
        row.status = entry.status
        row.base_url = entry.base_url
        row.last_checked_at = entry.last_checked_at
        row.entry_metadata = entry.entry_metadata
        row.updated_at = entry.updated_at
        await self._session.flush()

    async def list_all(self) -> list[ModelRegistryEntry]:
        rows = await self._session.scalars(select(ModelRegistryEntryOrm))
        return [_to_domain(row) for row in rows]
