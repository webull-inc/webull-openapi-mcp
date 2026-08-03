"""Screener market data tools for Webull MCP Server.

Provides:
- register_screener_tools: gainers/losers, most active (all regions).
- register_extended_screener_tools: market sectors, market sector detail,
  high dividend, 52-week high/low. All regions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from webull_openapi_mcp.errors import handle_sdk_exception
from webull_openapi_mcp.formatters import (
    extract_response_data,
    format_fifty_two_week,
    format_gainers_losers,
    format_high_dividend,
    format_market_sectors,
    format_market_sectors_detail,
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
    """Register screener market data tools."""

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


def register_extended_screener_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
) -> None:
    """Register extended screener tools (US / HK / JP only).

    Covers market sectors, market sector detail, high dividend, and 52-week
    high/low rankings.
    """

    @mcp.tool(
        description=(
            "Get market sector overview ranking. "
            "Returns per sector: id, name, change_ratio, volume, market_value, "
            "advanced, declined, flat, and a short list of leading stocks "
            "(symbol, name, instrument_id)."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_market_sectors(
        category: str = "US_STOCK",
        agg_type: Optional[str] = None,
        period: Optional[str] = None,
        page_index: Optional[int] = None,
        page_size: Optional[int] = None,
        direction: Optional[str] = None,
    ) -> str:
        """Get market sector overview ranking.

        Args:
            category: Security market category (e.g. US_STOCK).
            agg_type: Aggregation metric. MARKET_VALUE (default) or VOLUME.
            period: Time period. D1 (default), D5, M01, M03.
            page_index: Page number starting from 1.
            page_size: Records per page.
            direction: Sort direction. ASC or DESC.
        """
        audit.log_tool_call("get_market_sectors", {"category": category})
        try:
            data = extract_response_data(
                sdk.data.screener.get_market_sectors(
                    category=category,
                    agg_type=agg_type,
                    period=period,
                    page_index=page_index,
                    page_size=page_size,
                    direction=direction,
                )
            )
            return prepend_disclaimer(format_market_sectors(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_market_sectors", config.region_id)

    @mcp.tool(
        description=(
            "Get the stock list and statistics for a specific market sector. "
            "Returns: sector id, name, change_ratio, advanced/declined/flat counts, "
            "and a list of stocks with symbol, name, price, close, change_ratio, "
            "volume, market_value, turnover_rate, amplitude, high, low."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_market_sectors_detail(
        sector_id: str,
        category: str = "US_STOCK",
        period: Optional[str] = None,
        page_index: Optional[int] = None,
        page_size: Optional[int] = None,
        sort_by: Optional[str] = None,
        direction: Optional[str] = None,
    ) -> str:
        """Get stock list and statistics for a sector.

        Args:
            sector_id: Sector identifier (from get_market_sectors).
            category: Security market category (e.g. US_STOCK).
            period: Time period. D1 (default), D5, M01, M03.
            page_index: Page number starting from 1.
            page_size: Records per page.
            sort_by: Sort field. Default CHANGE_RATIO. Options include CHANGE_RATIO,
                RELATIVE_VOLUME_10D, MARKET_VALUE, CLOSE, PRICE, PE_TTM, HIGH, LOW,
                AMPLITUDE, TURNOVER, VOLUME, YIELD, DIVIDEND.
            direction: Sort direction. ASC or DESC.
        """
        audit.log_tool_call("get_market_sectors_detail", {"sector_id": sector_id})
        try:
            data = extract_response_data(
                sdk.data.screener.get_market_sectors_detail(
                    sector_id=sector_id,
                    category=category,
                    period=period,
                    page_index=page_index,
                    page_size=page_size,
                    sort_by=sort_by,
                    direction=direction,
                )
            )
            return prepend_disclaimer(format_market_sectors_detail(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_market_sectors_detail", config.region_id)

    @mcp.tool(
        description=(
            "Get high dividend stocks ranking. "
            "Returns: instrument_id, symbol, name, price, change_ratio, volume, "
            "market_value, yield, dividend, ex_date, pe_ttm."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_high_dividend(
        category: str = "US_STOCK",
        sort_by: Optional[str] = None,
        page_index: Optional[int] = None,
        page_size: Optional[int] = None,
        direction: Optional[str] = None,
    ) -> str:
        """Get high dividend stocks ranking.

        Args:
            category: Security market category (e.g. US_STOCK).
            sort_by: Sort field. Default YIELD. Options include CHANGE_RATIO,
                RELATIVE_VOLUME_10D, MARKET_VALUE, CLOSE, PRICE, PE_TTM, HIGH, LOW,
                AMPLITUDE, TURNOVER, VOLUME, YIELD, DIVIDEND.
            page_index: Page number starting from 1.
            page_size: Records per page.
            direction: Sort direction. ASC or DESC.
        """
        audit.log_tool_call("get_high_dividend", {"category": category})
        try:
            data = extract_response_data(
                sdk.data.screener.get_high_dividend(
                    category=category,
                    sort_by=sort_by,
                    page_index=page_index,
                    page_size=page_size,
                    direction=direction,
                )
            )
            return prepend_disclaimer(format_high_dividend(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_high_dividend", config.region_id)

    @mcp.tool(
        description=(
            "Get 52-week high/low stocks ranking. "
            "Returns: instrument_id, symbol, name, price, change_ratio, "
            "change_ratio_52w, price_1w, price_52w, high, low, pe_ttm."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_52_week_high_low(
        category: str = "US_STOCK",
        rank_type: Optional[str] = None,
        sort_by: Optional[str] = None,
        page_index: Optional[int] = None,
        page_size: Optional[int] = None,
        direction: Optional[str] = None,
    ) -> str:
        """Get 52-week high/low stocks ranking.

        Args:
            category: Security market category (e.g. US_STOCK).
            rank_type: Index code. NEW_HIGH, NEAR_HIGH, NEW_LOW, NEAR_LOW.
            sort_by: Sort field. Default CHANGE_RATIO_52W. Options include CHANGE_RATIO,
                RELATIVE_VOLUME_10D, MARKET_VALUE, CLOSE, PRICE, PE_TTM, HIGH, LOW,
                AMPLITUDE, TURNOVER, VOLUME, YIELD, DIVIDEND.
            page_index: Page number starting from 1.
            page_size: Records per page.
            direction: Sort direction. ASC or DESC.
        """
        audit.log_tool_call("get_52_week_high_low", {"category": category, "rank_type": rank_type})
        try:
            data = extract_response_data(
                sdk.data.screener.get_52whl(
                    category=category,
                    rank_type=rank_type,
                    sort_by=sort_by,
                    page_index=page_index,
                    page_size=page_size,
                    direction=direction,
                )
            )
            return prepend_disclaimer(format_fifty_two_week(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_52_week_high_low", config.region_id)
