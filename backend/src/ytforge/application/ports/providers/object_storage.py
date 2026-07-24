from __future__ import annotations

from typing import Protocol


class ObjectStorage(Protocol):
    """MinIO-backed object storage (ARCHITECTURE.md §6.3) — the only thing
    that ever writes/reads asset bytes. Media-producing agents call this
    directly after a provider call returns bytes (or a provider-hosted URL
    to download and re-host) so an `Asset.object_key` always resolves to
    something this app controls, never a third-party URL that can expire.
    `bucket` is the logical bucket name (`settings.minio.buckets` values —
    e.g. "raw-assets", "renders"), not a full URL."""

    async def put_object(self, bucket: str, key: str, data: bytes, content_type: str) -> None: ...
    async def get_object(self, bucket: str, key: str) -> bytes: ...
    async def presigned_url(self, bucket: str, key: str, ttl_seconds: int = 3600) -> str: ...
