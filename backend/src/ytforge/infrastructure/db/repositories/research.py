from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.application.common.pagination import Page, PageParams
from ytforge.domain.entities import ResearchDocument
from ytforge.infrastructure.db.models import ResearchDocument as ResearchDocumentOrm
from ytforge.infrastructure.db.repositories._pagination import paginate


def _to_domain(row: ResearchDocumentOrm) -> ResearchDocument:
    return ResearchDocument(
        id=row.id,
        project_id=row.project_id,
        source_url=row.source_url,
        title=row.title,
        content=row.content,
        citation=row.citation,
        qdrant_point_id=row.qdrant_point_id,
        published_at=row.published_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyResearchDocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, document_id: uuid.UUID) -> ResearchDocument | None:
        row = await self._session.get(ResearchDocumentOrm, document_id)
        return _to_domain(row) if row is not None else None

    async def add(self, document: ResearchDocument) -> None:
        row = ResearchDocumentOrm(
            id=document.id,
            project_id=document.project_id,
            source_url=document.source_url,
            title=document.title,
            content=document.content,
            citation=document.citation,
            qdrant_point_id=document.qdrant_point_id,
            published_at=document.published_at,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def list_for_project(
        self, project_id: uuid.UUID, params: PageParams
    ) -> Page[ResearchDocument]:
        stmt = (
            select(ResearchDocumentOrm)
            .where(ResearchDocumentOrm.project_id == project_id)
            .order_by(ResearchDocumentOrm.created_at.desc())
        )
        return await paginate(self._session, stmt, params, _to_domain)
