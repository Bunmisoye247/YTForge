from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from ytforge.application.common.pagination import Page


class PageResponse[T: BaseModel](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int

    @classmethod
    def from_page(cls, page: Page[Any], item_schema: type[T]) -> PageResponse[T]:
        return cls(
            items=[item_schema.model_validate(item) for item in page.items],
            total=page.total,
            limit=page.limit,
            offset=page.offset,
        )
