from __future__ import annotations

from fastapi import APIRouter

from ytforge.infrastructure.config.settings import get_settings
from ytforge.interfaces.api.deps.auth import CurrentUser
from ytforge.interfaces.api.schemas.settings import (
    AppSettingsRead,
    DatabaseSettingsRead,
    EffectiveSettingsRead,
    SecuritySettingsRead,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=EffectiveSettingsRead)
async def get_effective_settings(user: CurrentUser) -> EffectiveSettingsRead:
    """Read-only view of the merged config with secrets redacted. Safe
    YAML-editing/hot-reload is a larger feature left for a later phase."""
    settings = get_settings()
    return EffectiveSettingsRead(
        app=AppSettingsRead(
            name=settings.app.name,
            env=settings.app.env,
            debug=settings.app.debug,
            cors_origins=settings.app.cors_origins,
        ),
        database=DatabaseSettingsRead(
            host=settings.database.host,
            port=settings.database.port,
            name=settings.database.name,
            pool_size=settings.database.pool_size,
            echo=settings.database.echo,
        ),
        security=SecuritySettingsRead(
            access_token_ttl_minutes=settings.security.access_token_ttl_minutes,
            refresh_token_ttl_days=settings.security.refresh_token_ttl_days,
        ),
    )
