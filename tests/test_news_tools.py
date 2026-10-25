"""Unit tests for news formatters (news search, detail, stock news)."""

from __future__ import annotations

from webull_openapi_mcp.formatters import (
    format_news_detail,
    format_news_search,
    format_stock_news,
)


class TestFormatNewsSearch:
    def test_formats_list_with_pagination(self):
        data = {
            "keyword": "Starlink",
            "pagination_key": "1791348877000",
            "data": [
                {
                    "news_id": "15716519902127104",
                    "title": "Musk calls spectrum deal",
                    "source": "Benzinga",
                    "sentiment": "NEUTRAL",
                },
            ],
        }
        result = format_news_search(data)
        assert "=== News Keyword Search ===" in result
        assert "[1]" in result
        assert "Musk calls spectrum deal" in result
        assert "Benzinga" in result
        assert "Next pagination_key: 1791348877000" in result


class TestFormatNewsDetail:
    def test_skips_none_values(self):
        data = {"news_id": "1", "title": "Some title", "content": None}
        result = format_news_detail(data)
        assert "Some title" in result
        assert "content" not in result


class TestFormatStockNews:
    def test_formats_list_with_pagination(self):
        data = {
            "symbol": "TSLA",
            "next_pagination_key": "93f2c01a6c532f80ea",
            "data": [{"news_id": "15716519902127104", "title": "some title"}],
        }
        result = format_stock_news(data)
        assert "=== Stock News List ===" in result
        assert "some title" in result
        assert "Next pagination_key: 93f2c01a6c532f80ea" in result
