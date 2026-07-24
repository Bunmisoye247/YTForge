from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PageParams:
    limit: int = 50
    offset: int = 0

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        if self.offset < 0:
            raise ValueError("offset cannot be negative")


@dataclass(slots=True)
class Page[T]:
    items: list[T]
    total: int
    limit: int
    offset: int
