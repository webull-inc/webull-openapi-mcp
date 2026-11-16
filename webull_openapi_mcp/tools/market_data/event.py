"""Event contract market data tools for Webull MCP Server.

Provides: get_event_tick, get_event_snapshot, get_event_depth, get_event_bars.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from webull_openapi_mcp.errors import handle_sdk_exception
from webull_openapi_mcp.formatters import (
    extract_response_data,
    format_event_bars,
    format_event_depth,
    format_event_snapshot,
    format_event_tick,
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


def register_event_market_data_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
) -> None:
    """Register event contract market data tools."""

    @mcp.tool(
        description=(
            "Get event contract tick-by-tick trade data. "
            "Returns: time, price, volume, side."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_event_tick(
        symbol: str,
        category: str = "US_EVENT",
        count: int = 30,
    ) -> str:
        """Fetch tick-by-tick trade data for an event contract."""
        audit.log_tool_call("get_event_tick", {"symbol": symbol})
        try:
            kwargs = _build_kwargs(
                {"symbol": symbol, "category": category},
                count=count if count != 30 else None,
            )
            data = extract_response_data(sdk.data.event_market_data.get_event_tick(**kwargs))
            return prepend_disclaimer(format_event_tick(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_event_tick", config.region_id)

    @mcp.tool(
        description=(
            "Get event contract real-time snapshot. "
            "Returns: symbol, price, change, change_ratio, volume, bid, ask."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_event_snapshot(
        symbols: str,
        category: str = "US_EVENT",
    ) -> str:
        """Fetch real-time event contract snapshot for one or more symbols."""
        audit.log_tool_call("get_event_snapshot", {"symbols": symbols})
        try:
            sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
            data = extract_response_data(
                sdk.data.event_market_data.get_event_snapshot(symbols=sym_list, category=category)
            )
            return prepend_disclaimer(format_event_snapshot(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_event_snapshot", config.region_id)

    @mcp.tool(
        description=(
            "Get event contract order book depth. "
            "Returns: symbol, bids, asks."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_event_depth(
        symbol: str,
        category: str = "US_EVENT",
        depth: int = 10,
    ) -> str:
        """Fetch order book depth for an event contract."""
        audit.log_tool_call("get_event_depth", {"symbol": symbol})
        try:
            kwargs = _build_kwargs(
                {"symbol": symbol, "category": category},
                depth=depth if depth != 10 else None,
            )
            data = extract_response_data(sdk.data.event_market_data.get_event_depth(**kwargs))
            return prepend_disclaimer(format_event_depth(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_event_depth", config.region_id)

    @mcp.tool(
        description=(
            "Get event contract OHLCV bars. "
            "start_time/end_time: optional range as timestamps in milliseconds. "
            "Returns: time, open, high, low, close, volume."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_event_bars(
        symbols: str,
        category: str = "US_EVENT",
        timespan: str = "D",
        count: int = 200,
        real_time_required: bool = False,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> str:
        """Fetch historical OHLCV bar data for event contracts.

        Args:
            start_time: Start timestamp in milliseconds (optional).
            end_time: End timestamp in milliseconds (optional).
        """
        audit.log_tool_call("get_event_bars", {"symbols": symbols})
        try:
            sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
            kwargs = _build_kwargs(
                {"symbols": sym_list, "timespan": timespan, "category": category},
                count=count if count != 200 else None,
                real_time_required=real_time_required,
                start_time=start_time,
                end_time=end_time,
            )
            data = extract_response_data(sdk.data.event_market_data.get_event_bars(**kwargs))
            return prepend_disclaimer(format_event_bars(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_event_bars", config.region_id)
