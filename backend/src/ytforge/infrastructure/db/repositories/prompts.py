from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.application.common.pagination import Page, PageParams
from ytforge.domain.entities import PromptRun, PromptTemplate, PromptVersion
from ytforge.infrastructure.db.models import PromptRun as PromptRunOrm
from ytforge.infrastructure.db.models import PromptTemplate as PromptTemplateOrm
from ytforge.infrastructure.db.models import PromptVersion as PromptVersionOrm
from ytforge.infrastructure.db.repositories._pagination import paginate


def _template_to_domain(row: PromptTemplateOrm) -> PromptTemplate:
    return PromptTemplate(
        id=row.id, agent=row.agent, name=row.name, created_at=row.created_at, updated_at=row.updated_at
    )


def _version_to_domain(row: PromptVersionOrm) -> PromptVersion:
    return PromptVersion(
        id=row.id,
        template_id=row.template_id,
        version=row.version,
        content=row.content,
        front_matter=row.front_matter,
        model_hints=row.model_hints,
        variables=row.variables,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _run_to_domain(row: PromptRunOrm) -> PromptRun:
    return PromptRun(
        id=row.id,
        prompt_version_id=row.prompt_version_id,
        project_id=row.project_id,
        input_variables=row.input_variables,
        rendered_prompt=row.rendered_prompt,
        model_used=row.model_used,
        status=row.status,
        response=row.response,
        latency_ms=row.latency_ms,
        cost_usd=row.cost_usd,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyPromptTemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, template_id: uuid.UUID) -> PromptTemplate | None:
        row = await self._session.get(PromptTemplateOrm, template_id)
        return _template_to_domain(row) if row is not None else None

    async def get_by_agent_and_name(self, agent: str, name: str) -> PromptTemplate | None:
        stmt = select(PromptTemplateOrm).where(
            PromptTemplateOrm.agent == agent, PromptTemplateOrm.name == name
        )
        row = await self._session.scalar(stmt)
        return _template_to_domain(row) if row is not None else None

    async def add(self, template: PromptTemplate) -> None:
        row = PromptTemplateOrm(
            id=template.id,
            agent=template.agent,
            name=template.name,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def list_all(self) -> list[PromptTemplate]:
        rows = await self._session.scalars(select(PromptTemplateOrm))
        return [_template_to_domain(row) for row in rows]


class SqlAlchemyPromptVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, version: PromptVersion) -> None:
        row = PromptVersionOrm(
            id=version.id,
            template_id=version.template_id,
            version=version.version,
            content=version.content,
            front_matter=version.front_matter,
            model_hints=version.model_hints,
            variables=version.variables,
            created_at=version.created_at,
            updated_at=version.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def get_latest(self, template_id: uuid.UUID) -> PromptVersion | None:
        stmt = (
            select(PromptVersionOrm)
            .where(PromptVersionOrm.template_id == template_id)
            .order_by(PromptVersionOrm.version.desc())
            .limit(1)
        )
        row = await self._session.scalar(stmt)
        return _version_to_domain(row) if row is not None else None

    async def list_for_template(self, template_id: uuid.UUID) -> list[PromptVersion]:
        stmt = (
            select(PromptVersionOrm)
            .where(PromptVersionOrm.template_id == template_id)
            .order_by(PromptVersionOrm.version)
        )
        rows = await self._session.scalars(stmt)
        return [_version_to_domain(row) for row in rows]


class SqlAlchemyPromptRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, run: PromptRun) -> None:
        row = PromptRunOrm(
            id=run.id,
            prompt_version_id=run.prompt_version_id,
            project_id=run.project_id,
            input_variables=run.input_variables,
            rendered_prompt=run.rendered_prompt,
            response=run.response,
            model_used=run.model_used,
            status=run.status,
            latency_ms=run.latency_ms,
            cost_usd=run.cost_usd,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def list_for_version(
        self, prompt_version_id: uuid.UUID, params: PageParams
    ) -> Page[PromptRun]:
        stmt = (
            select(PromptRunOrm)
            .where(PromptRunOrm.prompt_version_id == prompt_version_id)
            .order_by(PromptRunOrm.created_at.desc())
        )
        return await paginate(self._session, stmt, params, _run_to_domain)

    async def sum_cost_for_project(self, project_id: uuid.UUID) -> Decimal:
        stmt = select(func.coalesce(func.sum(PromptRunOrm.cost_usd), 0)).where(
            PromptRunOrm.project_id == project_id
        )
        total = await self._session.scalar(stmt)
        return total if total is not None else Decimal("0")
