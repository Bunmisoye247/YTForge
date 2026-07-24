from __future__ import annotations

import uuid

from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import PromptTemplate, PromptVersion


async def list_prompt_templates(uow: UnitOfWork) -> list[PromptTemplate]:
    return await uow.prompt_templates.list_all()


async def list_prompt_versions(uow: UnitOfWork, template_id: uuid.UUID) -> list[PromptVersion]:
    return await uow.prompt_versions.list_for_template(template_id)
