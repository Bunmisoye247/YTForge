from __future__ import annotations

from ytforge.infrastructure.config.settings import get_settings
from ytforge.infrastructure.db.session import get_session_factory
from ytforge.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from ytforge.infrastructure.providers.discovery import run_discovery


async def detect_models() -> None:
    """Manual trigger for the same local-model-server scan the `local-ai`
    compose profile's Ollama/LM Studio/ComfyUI endpoints get auto-detected
    against — useful right after `docker compose --profile local-ai up`
    to populate `model_registry` without waiting for whatever future
    scheduled trigger runs this automatically."""
    settings = get_settings()
    uow = SqlAlchemyUnitOfWork(get_session_factory())
    async with uow:
        await run_discovery(uow, settings.models.discovery)
    print("model discovery complete")
