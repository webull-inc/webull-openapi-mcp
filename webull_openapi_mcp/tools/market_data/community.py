"""Community market data tools for Webull MCP Server.

Provides register_community_tools covering the community capabilities:
- create_community_post / create_community_comment (write operations)
- get_community_hot_stocks
- get_community_posts
- get_community_post_detail
- get_my_community_posts

All operations route to the published SDK ``sdk.data.community`` namespace.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from webull_openapi_mcp.errors import handle_sdk_exception
from webull_openapi_mcp.formatters import (
    extract_response_data,
    format_community_create_result,
    format_community_hot_stocks,
    format_community_post_detail,
    format_community_post_list,
    prepend_disclaimer,
)

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from webull_openapi_mcp.audit import AuditLogger
    from webull_openapi_mcp.config import ServerConfig
    from webull_openapi_mcp.sdk_client import WebullSDKClient


def register_community_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
) -> None:
    """Register community tools (posts, comments, hot stocks)."""

    @mcp.tool(
        description=(
            "Create a plain-text community post. Optionally attach a ticker by "
            "providing both symbol and category together. "
            "This is a write operation that publishes content under the user's account. "
            "Returns: post_id."
        ),
    )
    async def create_community_post(
        text: str,
        symbol: Optional[str] = None,
        category: Optional[str] = None,
    ) -> str:
        """Create a plain-text community post.

        Args:
            text: Post content.
            symbol: Optional ticker symbol. Must be provided together with category.
            category: Optional market category (e.g. US_STOCK, US_ETF).
                Must be provided together with symbol.
        """
        audit.log_tool_call("create_community_post", {"symbol": symbol, "category": category})
        # symbol 与 category 必须成对提供；用真值判断使空串与 None 都视为未提供，
        # 并把空串归一化为 None，避免把空值发给 SDK。
        symbol = symbol or None
        category = category or None
        if (symbol is None) != (category is None):
            return "Validation error: symbol and category must be provided together."
        try:
            data = extract_response_data(
                sdk.data.community.create_post(text, symbol=symbol, category=category)
            )
            return prepend_disclaimer(format_community_create_result(data))
        except Exception as e:
            return handle_sdk_exception(e, "create_community_post", config.region_id)

    @mcp.tool(
        description=(
            "Create a plain-text comment on an existing community post. "
            "This is a write operation that publishes content under the user's account. "
            "Returns: comment_id."
        ),
    )
    async def create_community_comment(
        post_id: str,
        text: str,
    ) -> str:
        """Create a plain-text comment on a community post.

        Args:
            post_id: Parent post identifier.
            text: Comment content.
        """
        audit.log_tool_call("create_community_comment", {"post_id": post_id})
        try:
            data = extract_response_data(
                sdk.data.community.create_comment(post_id, text)
            )
            return prepend_disclaimer(format_community_create_result(data))
        except Exception as e:
            return handle_sdk_exception(e, "create_community_comment", config.region_id)

    @mcp.tool(
        description=(
            "List stocks ranked by community activity (hot stocks). "
            "Returns: rank, symbol, category."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_community_hot_stocks() -> str:
        """List stocks ranked by community activity."""
        audit.log_tool_call("get_community_hot_stocks", {})
        try:
            data = extract_response_data(sdk.data.community.list_hot_stocks())
            return prepend_disclaimer(format_community_hot_stocks(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_community_hot_stocks", config.region_id)

    @mcp.tool(
        description=(
            "List community posts associated with a symbol. Supports keyword search "
            "and cursor pagination. "
            "Returns: post_id, text, publish_time, thumbs, comments, and a pagination_key."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_community_posts(
        symbol: str,
        category: str,
        keyword: Optional[str] = None,
        pagination_key: Optional[str] = None,
    ) -> str:
        """List community posts associated with a symbol.

        Args:
            symbol: Stock symbol.
            category: Market category (e.g. US_STOCK, US_ETF).
            keyword: Optional search keyword.
            pagination_key: Optional cursor from the previous response.
        """
        audit.log_tool_call(
            "get_community_posts", {"symbol": symbol, "category": category}
        )
        try:
            data = extract_response_data(
                sdk.data.community.list_posts_by_symbol(
                    symbol, category, keyword=keyword, pagination_key=pagination_key
                )
            )
            return prepend_disclaimer(format_community_post_list(data, title="Posts by Symbol"))
        except Exception as e:
            return handle_sdk_exception(e, "get_community_posts", config.region_id)

    @mcp.tool(
        description=(
            "Get detailed information for a community post, including attached tickers. "
            "Returns: post_id, text, publish_time, thumbs, comments, tickers."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_community_post_detail(post_id: str) -> str:
        """Get detailed information for a community post.

        Args:
            post_id: Post identifier.
        """
        audit.log_tool_call("get_community_post_detail", {"post_id": post_id})
        try:
            data = extract_response_data(sdk.data.community.get_post(post_id))
            return prepend_disclaimer(format_community_post_detail(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_community_post_detail", config.region_id)

    @mcp.tool(
        description=(
            "List posts created by the current user. Supports cursor pagination. "
            "Returns: post_id, text, publish_time, thumbs, comments, and a pagination_key."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_my_community_posts(
        pagination_key: Optional[str] = None,
    ) -> str:
        """List posts created by the current user.

        Args:
            pagination_key: Optional cursor from the previous response.
        """
        audit.log_tool_call("get_my_community_posts", {})
        try:
            data = extract_response_data(
                sdk.data.community.list_my_posts(pagination_key=pagination_key)
            )
            return prepend_disclaimer(format_community_post_list(data, title="My Posts"))
        except Exception as e:
            return handle_sdk_exception(e, "get_my_community_posts", config.region_id)
