from __future__ import annotations

from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import ModelRegistryEntry


async def list_models(uow: UnitOfWork) -> list[ModelRegistryEntry]:
    return await uow.model_registry.list_all()
