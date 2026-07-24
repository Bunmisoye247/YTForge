from __future__ import annotations

from datetime import date
from decimal import Decimal

import httpx
import pytest
import respx

from ytforge.infrastructure.external.youtube.analytics_api import YouTubeAnalyticsApiClient


@respx.mock
async def test_fetch_daily_metrics_parses_row_by_column_headers() -> None:
    respx.get("https://youtubeanalytics.googleapis.com/v2/reports").mock(
        return_value=httpx.Response(
            200,
            json={
                "columnHeaders": [
                    {"name": "views"},
                    {"name": "estimatedMinutesWatched"},
                    {"name": "likes"},
                    {"name": "comments"},
                    {"name": "shares"},
                    {"name": "subscribersGained"},
                    {"name": "estimatedRevenue"},
                ],
                "rows": [[1000, 543.5, 42, 7, 3, 5, 1.23]],
            },
        )
    )

    result = await YouTubeAnalyticsApiClient().fetch_daily_metrics(
        access_token="access-1", youtube_video_id="yt-video-1", target_date=date(2026, 1, 15)
    )

    assert result.views == 1000
    assert result.watch_time_minutes == Decimal("543.5")
    assert result.likes == 42
    assert result.comments == 7
    assert result.shares == 3
    assert result.subscribers_gained == 5
    assert result.revenue_usd == Decimal("1.23")


@respx.mock
async def test_fetch_daily_metrics_returns_zeros_when_no_rows() -> None:
    respx.get("https://youtubeanalytics.googleapis.com/v2/reports").mock(
        return_value=httpx.Response(200, json={"columnHeaders": [{"name": "views"}], "rows": []})
    )

    result = await YouTubeAnalyticsApiClient().fetch_daily_metrics(
        access_token="access-1", youtube_video_id="yt-video-1", target_date=date(2026, 1, 15)
    )

    assert result.views == 0
    assert result.watch_time_minutes == Decimal("0")


@respx.mock
async def test_fetch_daily_metrics_returns_zeros_when_rows_key_missing() -> None:
    respx.get("https://youtubeanalytics.googleapis.com/v2/reports").mock(
        return_value=httpx.Response(200, json={"columnHeaders": [{"name": "views"}]})
    )

    result = await YouTubeAnalyticsApiClient().fetch_daily_metrics(
        access_token="access-1", youtube_video_id="yt-video-1", target_date=date(2026, 1, 15)
    )

    assert result.views == 0


@respx.mock
async def test_fetch_daily_metrics_sends_expected_query_params_and_auth_header() -> None:
    route = respx.get("https://youtubeanalytics.googleapis.com/v2/reports").mock(
        return_value=httpx.Response(200, json={"columnHeaders": [], "rows": []})
    )

    await YouTubeAnalyticsApiClient().fetch_daily_metrics(
        access_token="my-access-token", youtube_video_id="yt-video-42", target_date=date(2026, 3, 1)
    )

    sent = route.calls.last.request
    assert sent.headers["Authorization"] == "Bearer my-access-token"
    assert sent.url.params["ids"] == "channel==MINE"
    assert sent.url.params["startDate"] == "2026-03-01"
    assert sent.url.params["endDate"] == "2026-03-01"
    assert sent.url.params["filters"] == "video==yt-video-42"
    assert "views" in sent.url.params["metrics"]


@respx.mock
async def test_fetch_daily_metrics_raises_on_http_error() -> None:
    respx.get("https://youtubeanalytics.googleapis.com/v2/reports").mock(return_value=httpx.Response(401))

    with pytest.raises(httpx.HTTPStatusError):
        await YouTubeAnalyticsApiClient().fetch_daily_metrics(
            access_token="bad-token", youtube_video_id="yt-video-1", target_date=date(2026, 1, 15)
        )
