from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class DecodedToken:
    user_id: uuid.UUID
    token_version: int


class TokenService(Protocol):
    def issue_access_token(self, user_id: uuid.UUID) -> str: ...
    def issue_refresh_token(self, user_id: uuid.UUID, token_version: int) -> str: ...
    def decode_access_token(self, token: str) -> DecodedToken: ...
    def decode_refresh_token(self, token: str) -> DecodedToken: ...
