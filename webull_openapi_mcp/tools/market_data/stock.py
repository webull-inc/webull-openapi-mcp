"""Stock market data tools for Webull MCP Server.

Provides: get_stock_tick, get_stock_snapshot, get_stock_quotes,
          get_stock_footprint, get_stock_bars, get_stock_bars_single.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from webull_openapi_mcp.errors import handle_sdk_exception
from webull_openapi_mcp.formatters import (
    extract_response_data,
    format_noii_bars,
    format_noii_snapshot,
    format_stock_bars,
    format_stock_footprint,
    format_stock_quotes,
    format_stock_snapshot,
    format_stock_tick,
    prepend_disclaimer,
)

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from webull_openapi_mcp.audit import AuditLogger
    from webull_openapi_mcp.config import ServerConfig
    from webull_openapi_mcp.sdk_client import WebullSDKClient


def _build_kwargs(base: dict[str, Any], **optional: Any) -> dict[str, Any]:
    """Build kwargs dict, adding only non-None / truthy optional values."""
    for key, value in optional.items():
        if value is not None and value is not False:
            base[key] = value
    return base


def register_stock_market_data_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
) -> None:
    """Register stock market data tools."""

    @mcp.tool(
        description=(
            "Get stock tick-by-tick trade data. "
            "Returns: time, price, volume, side, trading_session."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_stock_tick(
        symbol: str,
        category: str = "US_STOCK",
        count: int = 30,
        trading_sessions: Optional[str] = None,
    ) -> str:
        """Get stock tick-by-tick trade data."""
        audit.log_tool_call("get_stock_tick", {"symbol": symbol})
        try:
            kwargs = _build_kwargs(
                {"symbol": symbol, "category": category, "count": str(count)},
                trading_sessions=trading_sessions,
            )
            data = extract_response_data(sdk.data.market_data.get_tick(**kwargs))
            return prepend_disclaimer(format_stock_tick(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_stock_tick", config.region_id)

    @mcp.tool(
        description=(
            "Get real-time stock/ETF snapshot. Supports multiple symbols. "
            "Returns: symbol, price, pre_close, open, high, low, close, volume, "
            "change, change_ratio, bid, ask, turnover, eps, eps_ttm, lot_size, bps, "
            "extend_hour, overnight data."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_stock_snapshot(
        symbols: str,
        category: str = "US_STOCK",
        extend_hour_required: bool = False,
        overnight_required: bool = False,
    ) -> str:
        """Get real-time stock/ETF snapshot."""
        audit.log_tool_call("get_stock_snapshot", {"symbols": symbols})
        try:
            sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
            kwargs = _build_kwargs(
                {"symbols": sym_list, "category": category},
                extend_hour_required=extend_hour_required,
                overnight_required=overnight_required,
            )
            data = extract_response_data(sdk.data.market_data.get_snapshot(**kwargs))
            return prepend_disclaimer(format_stock_snapshot(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_stock_snapshot", config.region_id)

    @mcp.tool(
        description=(
            "Get real-time stock bid/ask quotes with depth. Single symbol only. "
            "Returns: symbol, bid_price, bid_size, ask_price, ask_size."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_stock_quotes(
        symbol: str,
        category: str = "US_STOCK",
        depth: Optional[int] = None,
        overnight_required: bool = False,
    ) -> str:
        """Get real-time stock bid/ask quotes."""
        audit.log_tool_call("get_stock_quotes", {"symbol": symbol})
        try:
            kwargs = _build_kwargs(
                {"symbol": symbol, "category": category},
                depth=depth,
                overnight_required=overnight_required,
            )
            data = extract_response_data(sdk.data.market_data.get_quotes(**kwargs))
            return prepend_disclaimer(format_stock_quotes(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_stock_quotes", config.region_id)

    @mcp.tool(
        description=(
            "Get stock large order footprint (order flow). US_STOCK only. "
            "Returns: time, trading_session, total, delta, buy_total, sell_total, "
            "buy_detail, sell_detail."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_stock_footprint(
        symbols: str,
        category: str = "US_STOCK",
        timespan: str = "M1",
        count: int = 200,
        real_time_required: bool = False,
        trading_sessions: Optional[str] = None,
    ) -> str:
        """Get stock large order footprint data."""
        audit.log_tool_call("get_stock_footprint", {"symbols": symbols})
        try:
            sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
            kwargs = _build_kwargs(
                {"symbols": sym_list, "category": category, "timespan": timespan, "count": str(count)},
                real_time_required=real_time_required,
                trading_sessions=trading_sessions,
            )
            data = extract_response_data(sdk.data.market_data.get_footprint(**kwargs))
            return prepend_disclaimer(format_stock_footprint(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_stock_footprint", config.region_id)

    @mcp.tool(
        description=(
            "Get stock OHLCV bars in batch. Supports multiple symbols. "
            "Returns: time, open, high, low, close, volume."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_stock_bars(
        symbols: str,
        category: str = "US_STOCK",
        timespan: str = "D",
        count: int = 200,
        real_time_required: bool = False,
        trading_sessions: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> str:
        """Batch fetch historical OHLCV bar data for multiple stock symbols.

        Args:
            start_time: Start timestamp in milliseconds (optional).
            end_time: End timestamp in milliseconds (optional).
        """
        audit.log_tool_call("get_stock_bars", {"symbols": symbols})
        try:
            sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
            kwargs = _build_kwargs(
                {"symbols": sym_list, "category": category, "timespan": timespan, "count": str(count)},
                real_time_required=real_time_required,
                trading_sessions=trading_sessions,
                start_time=start_time,
                end_time=end_time,
            )
            data = extract_response_data(sdk.data.market_data.get_batch_history_bar(**kwargs))
            return prepend_disclaimer(format_stock_bars(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_stock_bars", config.region_id)

    @mcp.tool(
        description=(
            "Get OHLCV bars for a single stock. "
            "Returns: time, open, high, low, close, volume."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_stock_bars_single(
        symbol: str,
        category: str = "US_STOCK",
        timespan: str = "D",
        count: int = 200,
        real_time_required: bool = False,
        trading_sessions: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> str:
        """Fetch historical OHLCV bar data for a single stock symbol.

        Args:
            start_time: Start timestamp in milliseconds (optional).
            end_time: End timestamp in milliseconds (optional).
        """
        audit.log_tool_call("get_stock_bars_single", {"symbol": symbol})
        try:
            kwargs = _build_kwargs(
                {"symbol": symbol, "category": category, "timespan": timespan, "count": str(count)},
                real_time_required=real_time_required,
                trading_sessions=trading_sessions,
                start_time=start_time,
                end_time=end_time,
            )
            data = extract_response_data(sdk.data.market_data.get_history_bar(**kwargs))
            return prepend_disclaimer(format_stock_bars(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_stock_bars_single", config.region_id)

    @mcp.tool(
        description=(
            "Get NOII (Net Order Imbalance Indicator) K-line data for a stock. "
            "NOII is published by NASDAQ before opening and closing auctions. "
            "Returns: instrument_id, symbol, imbalance_time, imbalance_ref_price, "
            "imbalance_near_price, imbalance_far_price, imbalance_action_type."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_stock_noii_bars(
        symbol: str,
        category: str = "US_STOCK",
        imbalance_action_type: str = "PRE_OPEN",
    ) -> str:
        """Get NOII K-line data during opening/closing auctions.

        Args:
            imbalance_action_type: PRE_OPEN (opening imbalance) or PRE_CLOSE (closing imbalance).
        """
        audit.log_tool_call("get_stock_noii_bars", {"symbol": symbol, "imbalance_action_type": imbalance_action_type})
        try:
            data = extract_response_data(
                sdk.data.market_data.get_noii_bars(
                    symbol=symbol, category=category, imbalance_action_type=imbalance_action_type,
                )
            )
            return prepend_disclaimer(format_noii_bars(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_stock_noii_bars", config.region_id)

    @mcp.tool(
        description=(
            "Get latest NOII (Net Order Imbalance Indicator) snapshot for a stock. "
            "Provides real-time supply-demand data during US stock auction phases. "
            "Opening auction: 9:28-9:30 AM ET; Closing auction: 3:50-4:00 PM ET. "
            "Returns: instrument_id, paired_shares, imbalance_shares, imbalance_side, "
            "imbalance_ref_price, imbalance_near_price, imbalance_far_price."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_stock_noii_snapshot(
        symbol: str,
        category: str = "US_STOCK",
        imbalance_action_type: str = "PRE_OPEN",
    ) -> str:
        """Get latest NOII snapshot during opening/closing auctions.

        Args:
            imbalance_action_type: PRE_OPEN (opening imbalance) or PRE_CLOSE (closing imbalance).
        """
        audit.log_tool_call("get_stock_noii_snapshot", {"symbol": symbol, "imbalance_action_type": imbalance_action_type})
        try:
            data = extract_response_data(
                sdk.data.market_data.get_noii_snapshot(
                    symbol=symbol, category=category, imbalance_action_type=imbalance_action_type,
                )
            )
            return prepend_disclaimer(format_noii_snapshot(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_stock_noii_snapshot", config.region_id)
