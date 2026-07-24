from __future__ import annotations

from ytforge.infrastructure.storage.minio_storage import MinioObjectStorage


class _FakeMinioResponse:
    def __init__(self, data: bytes) -> None:
        self._data = data
        self.closed = False
        self.released = False

    def read(self) -> bytes:
        return self._data

    def close(self) -> None:
        self.closed = True

    def release_conn(self) -> None:
        self.released = True


class _FakeMinioClient:
    def __init__(self) -> None:
        self.buckets: set[str] = set()
        self.objects: dict[tuple[str, str], bytes] = {}
        self.made_bucket_calls: list[str] = []
        self.presign_calls: list[tuple[str, str]] = []

    def bucket_exists(self, bucket: str) -> bool:
        return bucket in self.buckets

    def make_bucket(self, bucket: str) -> None:
        self.made_bucket_calls.append(bucket)
        self.buckets.add(bucket)

    def put_object(self, bucket: str, key: str, data: object, length: int, content_type: str) -> None:
        assert bucket in self.buckets, "put_object called before bucket was ensured"
        self.objects[(bucket, key)] = data.read()  # type: ignore[attr-defined]

    def get_object(self, bucket: str, key: str) -> _FakeMinioResponse:
        return _FakeMinioResponse(self.objects[(bucket, key)])

    def presigned_get_object(self, bucket: str, key: str, expires: object) -> str:
        self.presign_calls.append((bucket, key))
        return f"https://minio.local/{bucket}/{key}?signed=1"


def _storage_with_fake_client() -> tuple[MinioObjectStorage, _FakeMinioClient]:
    storage = MinioObjectStorage(endpoint="localhost:9000", access_key="x", secret_key="y", secure=False)
    fake_client = _FakeMinioClient()
    storage._client = fake_client  # type: ignore[assignment]
    return storage, fake_client


async def test_put_object_creates_bucket_lazily_then_writes() -> None:
    storage, client = _storage_with_fake_client()

    await storage.put_object("raw-assets", "a1111/abc.png", b"hello", "image/png")

    assert client.made_bucket_calls == ["raw-assets"]
    assert client.objects[("raw-assets", "a1111/abc.png")] == b"hello"


async def test_put_object_does_not_recreate_bucket_on_second_call() -> None:
    storage, client = _storage_with_fake_client()

    await storage.put_object("raw-assets", "a.png", b"1", "image/png")
    await storage.put_object("raw-assets", "b.png", b"2", "image/png")

    assert client.made_bucket_calls == ["raw-assets"]


async def test_get_object_reads_and_releases_connection() -> None:
    storage, client = _storage_with_fake_client()
    client.buckets.add("raw-assets")
    client.objects[("raw-assets", "key.png")] = b"payload"

    data = await storage.get_object("raw-assets", "key.png")

    assert data == b"payload"


async def test_presigned_url_delegates_to_client() -> None:
    storage, client = _storage_with_fake_client()

    url = await storage.presigned_url("renders", "final.mp4", ttl_seconds=120)

    assert url == "https://minio.local/renders/final.mp4?signed=1"
    assert client.presign_calls == [("renders", "final.mp4")]
