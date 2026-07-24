from __future__ import annotations

import pytest

from ytforge.application.common.errors import NotFoundError
from ytforge.infrastructure.storage.fake import FakeObjectStorage


async def test_put_then_get_round_trips_bytes() -> None:
    storage = FakeObjectStorage()

    await storage.put_object("raw-assets", "a.png", b"hello", "image/png")

    assert await storage.get_object("raw-assets", "a.png") == b"hello"


async def test_get_missing_object_raises_not_found() -> None:
    storage = FakeObjectStorage()

    with pytest.raises(NotFoundError):
        await storage.get_object("raw-assets", "missing.png")


async def test_same_key_in_different_buckets_are_independent() -> None:
    storage = FakeObjectStorage()

    await storage.put_object("raw-assets", "a.png", b"raw", "image/png")
    await storage.put_object("renders", "a.png", b"rendered", "video/mp4")

    assert await storage.get_object("raw-assets", "a.png") == b"raw"
    assert await storage.get_object("renders", "a.png") == b"rendered"


async def test_presigned_url_is_deterministic_and_fake_scheme() -> None:
    storage = FakeObjectStorage()

    url = await storage.presigned_url("renders", "final.mp4")

    assert url == "fake://renders/final.mp4"
