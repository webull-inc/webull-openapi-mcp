"""News data tools for Webull MCP Server.

Provides register_news_tools: keyword news search, news detail, and
stock-related news list — US market data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from webull_openapi_mcp.errors import handle_sdk_exception
from webull_openapi_mcp.formatters import (
    extract_response_data,
    format_news_detail,
    format_news_search,
    format_stock_news,
    prepend_disclaimer,
)

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from webull_openapi_mcp.audit import AuditLogger
    from webull_openapi_mcp.config import ServerConfig
    from webull_openapi_mcp.sdk_client import WebullSDKClient


def register_news_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
) -> None:
    """Register news tools (search, detail, stock news — US market data)."""

    @mcp.tool(
        description=(
            "Search US market news by keyword. "
            "Returns: news list with news_id, title, summary, source, url, "
            "publish_time, sentiment, related_symbols."
        ),
        annotations={"readOnlyHint": True},
    )
    async def search_news(
        keyword: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        pagination_key: Optional[str] = None,
    ) -> str:
        """Search US market news by keyword.

        Args:
            keyword: Search keyword, max 100 characters.
            start_date: Start date in yyyy-MM-dd format. Defaults to 7 days ago.
            end_date: End date in yyyy-MM-dd format. Defaults to today.
            pagination_key: Pagination key from the previous page response;
                not returned on the last page.
        """
        audit.log_tool_call("search_news", {"keyword": keyword})
        try:
            data = extract_response_data(
                sdk.data.news.get_news_search(keyword, start_date, end_date, pagination_key)
            )
            return prepend_disclaimer(format_news_search(data))
        except Exception as e:
            return handle_sdk_exception(e, "search_news", config.region_id)

    @mcp.tool(
        description=(
            "Get the full content of a US market news article by its ID. "
            "Returns: news detail with title, summary, source, url, publish_time, "
            "sentiment, related_symbols, content."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_news_detail(news_id: str) -> str:
        """Get the full content of a US market news article.

        Args:
            news_id: News unique identifier.
        """
        audit.log_tool_call("get_news_detail", {"news_id": news_id})
        try:
            data = extract_response_data(sdk.data.news.get_news_detail(news_id))
            return prepend_disclaimer(format_news_detail(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_news_detail", config.region_id)

    @mcp.tool(
        description=(
            "Get US stock-related news list with optional sentiment filter. "
            "Returns: news list with news_id, title, summary, source, url, "
            "publish_time, sentiment, related_symbols."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_stock_news(
        symbol: str,
        sentiment: Optional[str] = None,
        pagination_key: Optional[str] = None,
    ) -> str:
        """Get stock-related news list.

        Args:
            symbol: Stock symbol (e.g. TSLA).
            sentiment: Sentiment filter. Valid values: POSITIVE, NEGATIVE,
                NEUTRAL. Default returns all.
            pagination_key: Pagination key from the previous page response;
                not returned on the last page.
        """
        audit.log_tool_call("get_stock_news", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.news.get_stock_news(
                    symbol,
                    category="US_STOCK",
                    sentiment=sentiment.upper() if sentiment else None,
                    pagination_key=pagination_key,
                )
            )
            return prepend_disclaimer(format_stock_news(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_stock_news", config.region_id)
