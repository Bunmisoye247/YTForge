from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from uuid6 import uuid7

from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import PromptTemplate, PromptVersion


@dataclass(frozen=True, slots=True)
class CreatePromptVersionInput:
    agent: str
    name: str
    content: str
    front_matter: dict[str, Any] = field(default_factory=dict)
    model_hints: dict[str, Any] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)


async def create_prompt_version(uow: UnitOfWork, data: CreatePromptVersionInput) -> PromptVersion:
    """Prompt versions are never edited in place — each call appends v{N+1}."""
    now = datetime.now(UTC)
    template = await uow.prompt_templates.get_by_agent_and_name(data.agent, data.name)
    if template is None:
        template = PromptTemplate(id=uuid7(), agent=data.agent, name=data.name, created_at=now, updated_at=now)
        await uow.prompt_templates.add(template)

    latest = await uow.prompt_versions.get_latest(template.id)
    next_version = 1 if latest is None else latest.version + 1

    version = PromptVersion(
        id=uuid7(),
        template_id=template.id,
        version=next_version,
        content=data.content,
        front_matter=data.front_matter,
        model_hints=data.model_hints,
        variables=data.variables,
        created_at=now,
        updated_at=now,
    )
    await uow.prompt_versions.add(version)
    await uow.commit()
    return version
