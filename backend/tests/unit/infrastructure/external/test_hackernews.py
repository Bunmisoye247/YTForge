from __future__ import annotations

import httpx
import respx

from ytforge.infrastructure.external.trends_sources.hackernews import HackerNewsTrendSource


@respx.mock
async def test_fetch_candidate_topics_returns_story_titles() -> None:
    respx.get("https://hacker-news.firebaseio.com/v0/topstories.json").mock(
        return_value=httpx.Response(200, json=[1, 2, 3])
    )
    respx.get("https://hacker-news.firebaseio.com/v0/item/1.json").mock(
        return_value=httpx.Response(200, json={"id": 1, "title": "First story"})
    )
    respx.get("https://hacker-news.firebaseio.com/v0/item/2.json").mock(
        return_value=httpx.Response(200, json={"id": 2, "title": "Second story"})
    )
    respx.get("https://hacker-news.firebaseio.com/v0/item/3.json").mock(
        return_value=httpx.Response(200, json={"id": 3, "title": "Third story"})
    )
    source = HackerNewsTrendSource()

    topics = await source.fetch_candidate_topics(limit=3)

    assert topics == ["First story", "Second story", "Third story"]


@respx.mock
async def test_fetch_candidate_topics_respects_limit() -> None:
    respx.get("https://hacker-news.firebaseio.com/v0/topstories.json").mock(
        return_value=httpx.Response(200, json=list(range(1, 20)))
    )
    for story_id in range(1, 3):
        respx.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json").mock(
            return_value=httpx.Response(200, json={"id": story_id, "title": f"Story {story_id}"})
        )
    source = HackerNewsTrendSource()

    topics = await source.fetch_candidate_topics(limit=2)

    assert len(topics) == 2


@respx.mock
async def test_fetch_candidate_topics_skips_items_with_no_title() -> None:
    respx.get("https://hacker-news.firebaseio.com/v0/topstories.json").mock(
        return_value=httpx.Response(200, json=[1, 2])
    )
    respx.get("https://hacker-news.firebaseio.com/v0/item/1.json").mock(
        return_value=httpx.Response(200, json={"id": 1, "title": "Has a title"})
    )
    respx.get("https://hacker-news.firebaseio.com/v0/item/2.json").mock(
        return_value=httpx.Response(200, json={"id": 2, "type": "job"})
    )
    source = HackerNewsTrendSource()

    topics = await source.fetch_candidate_topics(limit=2)

    assert topics == ["Has a title"]
