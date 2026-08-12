from __future__ import annotations

import asyncio
import io
from datetime import timedelta
from functools import partial

from minio import Minio
from minio.error import S3Error

from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call


class MinioObjectStorage:
    """MinIO adapter (ARCHITECTURE.md §6.3) — the `minio` SDK is
    synchronous, so every call runs in a thread via `asyncio.to_thread` to
    keep this a well-behaved async port implementation. Buckets are
    created lazily on first write, matching local-dev ergonomics (no
    separate bucket-provisioning step needed before the app can run)."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
        public_endpoint: str | None = None,
    ) -> None:
        self._client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        # Separate client purely for presigned-URL generation — MinIO signs
        # the URL against whatever host the client was built with, and that
        # host must be the browser-reachable one, not the docker-network-
        # internal `endpoint` every other call here uses.
        self._public_client = (
            self._client
            if public_endpoint is None
            else Minio(public_endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        )
        self._ensured_buckets: set[str] = set()

    async def _ensure_bucket(self, bucket: str) -> None:
        if bucket in self._ensured_buckets:
            return
        exists = await asyncio.to_thread(self._client.bucket_exists, bucket)
        if not exists:
            await asyncio.to_thread(self._client.make_bucket, bucket)
        self._ensured_buckets.add(bucket)

    async def put_object(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        async with record_provider_call("minio", "storage.put_object"):
            await self._ensure_bucket(bucket)
            await asyncio.to_thread(
                self._client.put_object,
                bucket,
                key,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )

    async def get_object(self, bucket: str, key: str) -> bytes:
        async with record_provider_call("minio", "storage.get_object"):
            response = await asyncio.to_thread(self._client.get_object, bucket, key)
            try:
                data: bytes = await asyncio.to_thread(response.read)
                return data
            finally:
                await asyncio.to_thread(response.close)
                await asyncio.to_thread(response.release_conn)

    async def presigned_url(self, bucket: str, key: str, ttl_seconds: int = 3600) -> str:
        async with record_provider_call("minio", "storage.presigned_url"):
            url: str = await asyncio.to_thread(
                partial(
                    self._public_client.presigned_get_object,
                    bucket,
                    key,
                    expires=timedelta(seconds=ttl_seconds),
                )
            )
            return url


__all__ = ["MinioObjectStorage", "S3Error"]
