from __future__ import annotations

from ytforge.application.common.errors import NotFoundError


class FakeObjectStorage:
    """In-memory stand-in for MinIO — no server needed for tests/fakeprovider
    runs. `presigned_url` returns a deterministic fake:// URL so callers can
    still assert on bucket/key without a real MinIO endpoint."""

    def __init__(self) -> None:
        self._objects: dict[tuple[str, str], bytes] = {}

    async def put_object(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        self._objects[(bucket, key)] = data

    async def get_object(self, bucket: str, key: str) -> bytes:
        try:
            return self._objects[(bucket, key)]
        except KeyError:
            raise NotFoundError("ObjectStorage", f"{bucket}/{key}") from None

    async def presigned_url(self, bucket: str, key: str, ttl_seconds: int = 3600) -> str:
        return f"fake://{bucket}/{key}"
