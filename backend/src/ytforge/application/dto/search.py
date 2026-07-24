from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SearchQuery:
    query: str
    max_results: int = 5


@dataclass(frozen=True, slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str
