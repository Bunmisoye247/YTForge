from __future__ import annotations

from typing import Annotated

from fastapi import Query

from ytforge.application.common.pagination import PageParams


def page_params(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PageParams:
    return PageParams(limit=limit, offset=offset)
