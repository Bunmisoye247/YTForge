from __future__ import annotations

from pathlib import Path

from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.use_cases.prompts import CreatePromptVersionInput, create_prompt_version
from ytforge.infrastructure.db.session import get_session_factory
from ytforge.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from ytforge.infrastructure.prompts.jinja_store import FilesystemPromptStore

PROMPTS_DIR = Path(__file__).resolve().parents[4] / "prompts"


async def sync_prompts() -> None:
    """Mirrors every `.v{N}.md.j2` file on disk into `prompt_templates`/
    `prompt_versions` via the existing Phase-4 use case, so the dashboard's
    Settings page reflects what's on disk (disk stays authoritative;
    rendering always reads from there directly, never from the DB)."""
    store = FilesystemPromptStore(PROMPTS_DIR)
    uow: UnitOfWork = SqlAlchemyUnitOfWork(get_session_factory())

    synced = 0
    async with uow:
        existing_versions: set[tuple[str, str, int]] = set()
        for template in await uow.prompt_templates.list_all():
            for version in await uow.prompt_versions.list_for_template(template.id):
                existing_versions.add((template.agent, template.name, version.version))

        for template_file in store.list_all_versions():
            key = (template_file.agent, template_file.name, template_file.version)
            if key in existing_versions:
                continue
            front_matter, body = store.read_front_matter_and_body(template_file.path)
            await create_prompt_version(
                uow,
                CreatePromptVersionInput(
                    agent=template_file.agent,
                    name=template_file.name,
                    content=body,
                    front_matter=front_matter,
                    model_hints=front_matter.get("model_hints", {}),
                    variables=front_matter.get("variables", {}),
                ),
            )
            synced += 1

    print(f"Synced {synced} new prompt version(s) from {PROMPTS_DIR}.")
