"""Unit tests for community formatters (posts, comments, hot stocks)."""

from __future__ import annotations

import pytest

from webull_openapi_mcp.formatters import (
    format_community_create_result,
    format_community_hot_stocks,
    format_community_post_detail,
    format_community_post_list,
)


_NO_DATA = "No data available."


# ---------------------------------------------------------------------------
# Empty / None data handling
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fn", [
    format_community_hot_stocks,
    format_community_post_list,
    format_community_post_detail,
])
def test_returns_no_data_for_none(fn):
    assert fn(None) == _NO_DATA


@pytest.mark.parametrize("fn", [
    format_community_hot_stocks,
    format_community_post_list,
])
def test_returns_no_data_for_empty_list(fn):
    assert fn([]) == _NO_DATA


# ---------------------------------------------------------------------------
# Create result (post / comment)
# ---------------------------------------------------------------------------

class TestFormatCreateResult:
    def test_formats_post_id(self):
        out = format_community_create_result({"post_id": "995005758239301632"})
        assert "Post ID: 995005758239301632" in out

    def test_formats_comment_id(self):
        out = format_community_create_result({"comment_id": "123456"})
        assert "Comment ID: 123456" in out

    def test_handles_unexpected_shape(self):
        # Non-dict / empty still produces a safe message rather than crashing.
        assert format_community_create_result(None) == "Operation completed."


# ---------------------------------------------------------------------------
# Hot stocks
# ---------------------------------------------------------------------------

class TestFormatHotStocks:
    def test_formats_ranking(self):
        data = {"data": [
            {"rank": 1, "symbol": "NVDA", "category": "US_STOCK"},
            {"rank": 2, "symbol": "AAPL", "category": "US_STOCK"},
        ]}
        out = format_community_hot_stocks(data)
        assert "Community Hot Stocks" in out
        assert "#1  NVDA  (US_STOCK)" in out
        assert "#2  AAPL  (US_STOCK)" in out

    def test_accepts_bare_list(self):
        out = format_community_hot_stocks([{"rank": 1, "symbol": "TSLA", "category": "US_STOCK"}])
        assert "TSLA" in out


# ---------------------------------------------------------------------------
# Post list (by symbol / my posts)
# ---------------------------------------------------------------------------

class TestFormatPostList:
    def test_formats_posts_and_pagination(self):
        data = {
            "data": [
                {"post_id": "1", "text": "hello", "publish_time": "2026-10-20",
                 "thumbs": 3, "comments": 1},
            ],
            "pagination_key": "cursor-abc",
        }
        out = format_community_post_list(data, title="Posts by Symbol")
        assert "Community Posts by Symbol" in out
        assert "Post ID: 1" in out
        assert "pagination_key=cursor-abc" in out

    def test_no_pagination_hint_when_absent(self):
        data = {"data": [{"post_id": "1", "text": "hi", "publish_time": "t",
                          "thumbs": 0, "comments": 0}]}
        out = format_community_post_list(data, title="My Posts")
        assert "pagination_key" not in out


# ---------------------------------------------------------------------------
# Post detail
# ---------------------------------------------------------------------------

class TestFormatPostDetail:
    def test_formats_detail_with_tickers(self):
        data = {
            "post_id": "995",
            "text": "great earnings",
            "publish_time": "2026-10-20",
            "thumbs": 10,
            "comments": 4,
            "tickers": [{"symbol": "NVDA", "category": "US_STOCK"}],
        }
        out = format_community_post_detail(data)
        assert "Community Post Detail" in out
        assert "Post ID: 995" in out
        assert "NVDA (US_STOCK)" in out

    def test_formats_detail_without_tickers(self):
        data = {"post_id": "1", "text": "x", "publish_time": "t",
                "thumbs": 0, "comments": 0}
        out = format_community_post_detail(data)
        assert "Post ID: 1" in out
        assert "Tickers:" not in out
