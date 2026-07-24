from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from uuid6 import uuid7

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import ResearchDocument


@dataclass(frozen=True, slots=True)
class AddResearchDocumentInput:
    project_id: uuid.UUID
    source_url: str
    title: str
    content: str
    citation: dict[str, Any] = field(default_factory=dict)
    published_at: datetime | None = None


async def add_research_document(
    uow: UnitOfWork, data: AddResearchDocumentInput
) -> ResearchDocument:
    if await uow.projects.get_by_id(data.project_id) is None:
        raise NotFoundError("Project", data.project_id)

    now = datetime.now(UTC)
    document = ResearchDocument(
        id=uuid7(),
        project_id=data.project_id,
        source_url=data.source_url,
        title=data.title,
        content=data.content,
        citation=data.citation,
        published_at=data.published_at,
        created_at=now,
        updated_at=now,
    )
    await uow.research_documents.add(document)
    await uow.commit()
    return document
