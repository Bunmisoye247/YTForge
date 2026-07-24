from __future__ import annotations

from typing import Protocol


class TrendSourceGateway(Protocol):
    """Feeds `TrendAgent`'s `candidate_topics` input (ARCHITECTURE.md §3 —
    "real trend-source fetchers ... aren't built" per `TrendAgent`'s own
    docstring). One real, keyless source (Hacker News) is built as of
    Phase 7; the other 6 named in the `TrendSource` enum (Google Trends,
    YouTube Trending, Reddit, X, RSS, News API) are left for follow-up."""

    async def fetch_candidate_topics(self, limit: int = 10) -> list[str]: ...
