from __future__ import annotations

from pydantic import BaseModel


class AppSettingsRead(BaseModel):
    name: str
    env: str
    debug: bool
    cors_origins: list[str]


class DatabaseSettingsRead(BaseModel):
    host: str
    port: int
    name: str
    pool_size: int
    echo: bool


class SecuritySettingsRead(BaseModel):
    access_token_ttl_minutes: int
    refresh_token_ttl_days: int


class EffectiveSettingsRead(BaseModel):
    app: AppSettingsRead
    database: DatabaseSettingsRead
    security: SecuritySettingsRead
