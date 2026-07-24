from __future__ import annotations

import asyncio

import httpx

_BASE_URL = "https://hacker-news.firebaseio.com/v0"
_TIMEOUT = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)


class HackerNewsTrendSource:
    """Free, unauthenticated Hacker News Firebase API — no API key needed,
    unlike every other named source in the `TrendSource` enum (Google
    Trends, YouTube Trending, Reddit, X, RSS, News API), which are left
    for follow-up. This is the one real, keyless source built for Phase 7
    so `TrendDiscoveryCronWorkflow` has genuine candidate topics rather
    than a vacuous loop."""

    async def fetch_candidate_topics(self, limit: int = 10) -> list[str]:
        async with httpx.AsyncClient(base_url=_BASE_URL, timeout=_TIMEOUT) as client:
            response = await client.get("/topstories.json")
            response.raise_for_status()
            story_ids: list[int] = response.json()[:limit]

            items = await asyncio.gather(*(self._fetch_title(client, story_id) for story_id in story_ids))
            return [title for title in items if title]

    async def _fetch_title(self, client: httpx.AsyncClient, story_id: int) -> str | None:
        response = await client.get(f"/item/{story_id}.json")
        response.raise_for_status()
        item = response.json()
        title: str | None = item.get("title") if item else None
        return title
