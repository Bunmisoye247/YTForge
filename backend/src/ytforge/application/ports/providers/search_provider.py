from __future__ import annotations

from typing import Protocol

from ytforge.application.dto.search import SearchQuery, SearchResult


class SearchProvider(Protocol):
    async def search(self, query: SearchQuery) -> list[SearchResult]: ...
