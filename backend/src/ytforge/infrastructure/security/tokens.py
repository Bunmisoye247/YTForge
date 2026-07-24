from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt

from ytforge.application.common.errors import AuthenticationError
from ytforge.application.ports.providers import DecodedToken
from ytforge.infrastructure.config.settings import SecuritySettings

_ALGORITHM = "HS256"
_TOKEN_TYPE_ACCESS = "access"
_TOKEN_TYPE_REFRESH = "refresh"


class JwtTokenService:
    def __init__(self, settings: SecuritySettings) -> None:
        self._secret = settings.jwt_secret.get_secret_value()
        self._access_ttl = timedelta(minutes=settings.access_token_ttl_minutes)
        self._refresh_ttl = timedelta(days=settings.refresh_token_ttl_days)

    def issue_access_token(self, user_id: uuid.UUID) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "type": _TOKEN_TYPE_ACCESS,
            "iat": now,
            "exp": now + self._access_ttl,
        }
        return jwt.encode(payload, self._secret, algorithm=_ALGORITHM)

    def issue_refresh_token(self, user_id: uuid.UUID, token_version: int) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "type": _TOKEN_TYPE_REFRESH,
            "token_version": token_version,
            "iat": now,
            "exp": now + self._refresh_ttl,
        }
        return jwt.encode(payload, self._secret, algorithm=_ALGORITHM)

    def decode_access_token(self, token: str) -> DecodedToken:
        return self._decode(token, expected_type=_TOKEN_TYPE_ACCESS)

    def decode_refresh_token(self, token: str) -> DecodedToken:
        return self._decode(token, expected_type=_TOKEN_TYPE_REFRESH)

    def _decode(self, token: str, *, expected_type: str) -> DecodedToken:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[_ALGORITHM])
        except jwt.PyJWTError as exc:
            raise AuthenticationError("invalid or expired token") from exc

        if payload.get("type") != expected_type:
            raise AuthenticationError("invalid token type")
        try:
            user_id = uuid.UUID(payload["sub"])
        except (KeyError, ValueError) as exc:
            raise AuthenticationError("invalid token subject") from exc

        return DecodedToken(user_id=user_id, token_version=payload.get("token_version", -1))
