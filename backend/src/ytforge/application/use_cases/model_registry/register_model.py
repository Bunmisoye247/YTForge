from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from uuid6 import uuid7

from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import ModelRegistryEntry
from ytforge.domain.enums import ModelAvailability, ModelCapability


@dataclass(frozen=True, slots=True)
class RegisterModelInput:
    provider: str
    model_name: str
    capability: ModelCapability
    base_url: str | None = None
    status: ModelAvailability = ModelAvailability.AVAILABLE
    entry_metadata: dict[str, Any] = field(default_factory=dict)


async def register_model(uow: UnitOfWork, data: RegisterModelInput) -> ModelRegistryEntry:
    """Manual registration. Auto-detection (ModelRouter discovery scan)
    lands in Phase 6."""
    now = datetime.now(UTC)
    entry = ModelRegistryEntry(
        id=uuid7(),
        provider=data.provider,
        model_name=data.model_name,
        capability=data.capability,
        status=data.status,
        discovered_at=now,
        base_url=data.base_url,
        last_checked_at=now,
        entry_metadata=data.entry_metadata,
        created_at=now,
        updated_at=now,
    )
    await uow.model_registry.add(entry)
    await uow.commit()
    return entry
