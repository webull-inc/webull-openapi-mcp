"""Screener market data tools for Webull MCP Server.

Provides: get_gainers_losers, get_most_active.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from webull_openapi_mcp.errors import handle_sdk_exception
from webull_openapi_mcp.formatters import (
    extract_response_data,
    format_gainers_losers,
    format_most_active,
    prepend_disclaimer,
)

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from webull_openapi_mcp.audit import AuditLogger
    from webull_openapi_mcp.config import ServerConfig
    from webull_openapi_mcp.sdk_client import WebullSDKClient


def register_screener_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
) -> None:
    """Register screener market data tools (US only)."""

    @mcp.tool(
        description=(
            "Get top gainers or losers ranking by price change. "
            "Use direction=DESC for gainers, direction=ASC for losers. "
            "Returns: instrument_id, symbol, name, price, change, change_ratio, volume, "
            "market_value, turnover_rate, amplitude."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_gainers_losers(
        rank_type: str = "DAY_1",
        category: str = "US_STOCK",
        sort_by: str = "CHANGE_RATIO",
        direction: str = "DESC",
        page_index: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> str:
        """Get stock top gainers or losers ranking.

        Args:
            rank_type: Time period. Values: PRE_MARKET, AFTER_MARKET, MIN_3, MIN_5,
                DAY_1, DAY_5, MONTH_1, MONTH_3, WEEK_52.
            sort_by: Secondary sort field. Values: CHANGE_RATIO, RELATIVE_VOLUME_10D,
                MARKET_VALUE, CLOSE, PRICE, PE_TTM, HIGH, LOW, AMPLITUDE, TURNOVER, VOLUME.
            direction: DESC for gainers (default), ASC for losers.
            page_index: Page number starting from 1.
            page_size: Records per page (default 20).
        """
        audit.log_tool_call("get_gainers_losers", {"rank_type": rank_type, "direction": direction})
        try:
            data = extract_response_data(
                sdk.data.screener.get_gainers_losers(
                    rank_type=rank_type,
                    category=category,
                    sort_by=sort_by,
                    page_index=page_index,
                    page_size=page_size,
                    direction=direction,
                )
            )
            return prepend_disclaimer(format_gainers_losers(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_gainers_losers", config.region_id)

    @mcp.tool(
        description=(
            "Get most actively traded stocks ranking. "
            "Ranked by volume, relative volume, turnover, turnover rate, or amplitude. "
            "Returns: instrument_id, symbol, name, price, change, change_ratio, volume, "
            "market_value, relative_volume_10d."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_most_active(
        category: str = "US_STOCK",
        rank_type: Optional[str] = None,
        sort_by: Optional[str] = None,
        direction: Optional[str] = None,
        page_index: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> str:
        """Get most actively traded stocks ranking.

        Args:
            rank_type: Activity metric. Values: VOLUME, RELATIVE_VOLUME_10D,
                TURNOVER, TURNOVER_RATE, AMPLITUDE. Default: VOLUME.
            sort_by: Secondary sort field. Values: CHANGE_RATIO, RELATIVE_VOLUME_10D,
                MARKET_VALUE, CLOSE, PRICE, PE_TTM, HIGH, LOW, AMPLITUDE, TURNOVER, VOLUME.
            direction: ASC or DESC (default DESC).
            page_index: Page number starting from 1.
            page_size: Records per page (default 20).
        """
        audit.log_tool_call("get_most_active", {"category": category, "rank_type": rank_type})
        try:
            data = extract_response_data(
                sdk.data.screener.get_most_active(
                    category=category,
                    rank_type=rank_type,
                    sort_by=sort_by,
                    page_index=page_index,
                    page_size=page_size,
                    direction=direction,
                )
            )
            return prepend_disclaimer(format_most_active(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_most_active", config.region_id)
