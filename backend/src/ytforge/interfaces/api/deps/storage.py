from __future__ import annotations

from functools import lru_cache

from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.config.settings import get_settings
from ytforge.infrastructure.storage.fake import FakeObjectStorage
from ytforge.infrastructure.storage.minio_storage import MinioObjectStorage


@lru_cache
def get_object_storage() -> ObjectStorage:
    settings = get_settings()
    if settings.models.provider_set == "fake":
        return FakeObjectStorage()
    return MinioObjectStorage(
        settings.minio.endpoint,
        settings.minio.access_key,
        settings.minio.secret_key.get_secret_value(),
        settings.minio.secure,
        settings.minio.public_endpoint,
    )
