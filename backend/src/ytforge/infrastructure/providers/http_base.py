from __future__ import annotations

from typing import Any

import httpx

from ytforge.infrastructure.providers.errors import (
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderRequestError,
)

_TIMEOUT = httpx.Timeout(connect=5.0, read=60.0, write=30.0, pool=5.0)


class ProviderHttpClient:
    """Thin wrapper every adapter builds once and reuses — maps HTTP status
    codes to the shared `ProviderError` hierarchy so `ModelRouter`'s
    fallback logic only needs to catch one exception family."""

    def __init__(self, provider: str, base_url: str, headers: dict[str, str] | None = None) -> None:
        self._provider = provider
        self._client = httpx.AsyncClient(base_url=base_url, headers=headers or {}, timeout=_TIMEOUT)

    async def post_json(self, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.post(path, json=json_body)
        return self._handle(response)

    async def get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = await self._client.get(path, params=params)
        return self._handle(response)

    def _handle(self, response: httpx.Response) -> dict[str, Any]:
        if response.status_code in (401, 403):
            raise ProviderAuthError(self._provider, f"HTTP {response.status_code}: {response.text[:200]}")
        if response.status_code == 429:
            raise ProviderRateLimitError(self._provider, f"rate limited: {response.text[:200]}")
        if response.status_code >= 400:
            raise ProviderRequestError(
                self._provider, f"HTTP {response.status_code}: {response.text[:200]}"
            )
        result: dict[str, Any] = response.json()
        return result

    async def aclose(self) -> None:
        await self._client.aclose()
