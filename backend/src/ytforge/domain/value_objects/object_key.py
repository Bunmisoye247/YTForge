from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ObjectKey:
    bucket: str
    key: str

    def __post_init__(self) -> None:
        if not self.bucket:
            raise ValueError("ObjectKey.bucket cannot be empty")
        if not self.key:
            raise ValueError("ObjectKey.key cannot be empty")

    @property
    def uri(self) -> str:
        return f"{self.bucket}/{self.key}"
