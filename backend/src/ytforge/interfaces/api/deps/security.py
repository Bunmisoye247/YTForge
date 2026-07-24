from __future__ import annotations

from functools import lru_cache

from ytforge.application.ports.providers import PasswordHasher, TokenService
from ytforge.infrastructure.config.settings import get_settings
from ytforge.infrastructure.security.passwords import Pbkdf2PasswordHasher
from ytforge.infrastructure.security.tokens import JwtTokenService


@lru_cache
def get_password_hasher() -> PasswordHasher:
    return Pbkdf2PasswordHasher()


@lru_cache
def get_token_service() -> TokenService:
    return JwtTokenService(get_settings().security)
