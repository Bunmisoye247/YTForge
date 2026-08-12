from __future__ import annotations

from typing import Any

import httpx

from ytforge.infrastructure.providers.errors import (
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderRequestError,
)

_TIMEOUT = httpx.Timeout(connect=5.0, read=60.0, write=30.0, pool=5.0)
# Deliberately much shorter than _TIMEOUT — a pre-flight health check that
# takes as long as a real generation call defeats its own purpose (failing
# fast before expensive work starts).
_HEALTH_TIMEOUT = httpx.Timeout(connect=3.0, read=5.0, write=3.0, pool=3.0)


class ProviderHttpClient:
    """Thin wrapper every adapter builds once and reuses — maps HTTP status
    codes to the shared `ProviderError` hierarchy so `ModelRouter`'s
    fallback logic only needs to catch one exception family."""

    def __init__(self, provider: str, base_url: str, headers: dict[str, str] | None = None) -> None:
        self._provider = provider
        self._client = httpx.AsyncClient(base_url=base_url, headers=headers or {}, timeout=_TIMEOUT)

    async def post_json(self, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await self._client.post(path, json=json_body)
        except httpx.HTTPError as exc:
            raise ProviderRequestError(self._provider, f"connection failed: {exc}") from exc
        return self._handle(response)

    async def get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = await self._client.get(path, params=params)
        except httpx.HTTPError as exc:
            raise ProviderRequestError(self._provider, f"connection failed: {exc}") from exc
        return self._handle(response)

    async def get_bytes(self, path: str, params: dict[str, Any] | None = None) -> bytes:
        """For adapters where the provider's own base_url returns a raw
        binary body directly (e.g. Pollinations' image endpoint), unlike
        get_json's JSON responses or the download-then-upload pattern used
        for third-party CDN URLs elsewhere."""
        try:
            response = await self._client.get(path, params=params)
        except httpx.HTTPError as exc:
            raise ProviderRequestError(self._provider, f"connection failed: {exc}") from exc
        self._check_status(response)
        return response.content

    async def post_bytes(
        self, path: str, json_body: dict[str, Any], params: dict[str, Any] | None = None
    ) -> bytes:
        """POST variant of get_bytes — for adapters whose synthesis/
        generation endpoint returns raw binary directly rather than a
        JSON envelope (e.g. Kokoro's ElevenLabs-shaped TTS endpoint)."""
        try:
            response = await self._client.post(path, json=json_body, params=params)
        except httpx.HTTPError as exc:
            raise ProviderRequestError(self._provider, f"connection failed: {exc}") from exc
        self._check_status(response)
        return response.content

    def _check_status(self, response: httpx.Response) -> None:
        if response.status_code in (401, 403):
            raise ProviderAuthError(self._provider, f"HTTP {response.status_code}: {response.text[:200]}")
        if response.status_code == 429:
            raise ProviderRateLimitError(self._provider, f"rate limited: {response.text[:200]}")
        if response.status_code >= 400:
            raise ProviderRequestError(
                self._provider, f"HTTP {response.status_code}: {response.text[:200]}"
            )

    def _handle(self, response: httpx.Response) -> dict[str, Any]:
        self._check_status(response)
        result: dict[str, Any] = response.json()
        return result

    async def ping(self, path: str, params: dict[str, Any] | None = None) -> None:
        """Cheap reachability/auth probe for workflow pre-flight health
        checks (short timeout; response body isn't parsed as JSON since
        some providers' lightweight status endpoints return plain text)."""
        try:
            response = await self._client.get(path, params=params, timeout=_HEALTH_TIMEOUT)
        except httpx.HTTPError as exc:
            raise ProviderRequestError(self._provider, f"health check failed: {exc}") from exc
        self._check_status(response)

    async def aclose(self) -> None:
        await self._client.aclose()
