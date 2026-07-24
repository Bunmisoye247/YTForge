from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt

from ytforge.application.common.errors import AuthenticationError

_ALGORITHM = "HS256"
_STATE_TTL = timedelta(minutes=10)


def sign_oauth_state(secret: str, channel_id: uuid.UUID) -> str:
    """Signs the OAuth `state` param with the existing JWT secret (no new
    secret needed) so the callback — which Google redirects to without any
    of our auth headers — can verify which channel initiated the flow and
    that the request wasn't tampered with or replayed after expiry."""
    now = datetime.now(UTC)
    payload = {"channel_id": str(channel_id), "iat": now, "exp": now + _STATE_TTL}
    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def verify_oauth_state(secret: str, state: str) -> uuid.UUID:
    try:
        payload = jwt.decode(state, secret, algorithms=[_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise AuthenticationError("invalid or expired oauth state") from exc
    try:
        return uuid.UUID(payload["channel_id"])
    except (KeyError, ValueError) as exc:
        raise AuthenticationError("invalid oauth state payload") from exc
