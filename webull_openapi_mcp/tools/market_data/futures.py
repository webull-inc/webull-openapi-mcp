"""Futures market data tools for Webull MCP Server.

Provides: get_futures_tick, get_futures_snapshot, get_futures_depth,
          get_futures_bars, get_futures_footprint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from webull_openapi_mcp.errors import handle_sdk_exception
from webull_openapi_mcp.formatters import (
    extract_response_data,
    format_futures_bars,
    format_futures_depth,
    format_futures_footprint,
    format_futures_snapshot,
    format_futures_tick,
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


def register_futures_market_data_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
) -> None:
    """Register futures market data tools."""
    from webull_openapi_mcp.region_config import get_region_config

    region_config = get_region_config(config.region_id)

    # HK region supports both US_FUTURES and HK_FUTURES, no default — require explicit input.
    # US region only has US_FUTURES, keep default value.
    if region_config.region_id == "hk":
        _valid_categories = "US_FUTURES, HK_FUTURES"
        _category_note = f"category (REQUIRED): {_valid_categories}."
    else:
        _valid_categories = "US_FUTURES"
        _category_note = f"category: {_valid_categories}."

    # HK region: category has no default (required); US region: defaults to "US_FUTURES"
    _default_category: str | None = None if region_config.region_id == "hk" else "US_FUTURES"

    def _validate_category(category: str | None) -> str | None:
        """Validate category, return error message or None."""
        if category is None:
            return (
                f"Validation error: category is required for {config.region_id.upper()} region. "
                f"Valid values: {_valid_categories}."
            )
        return None

    @mcp.tool(
        description=(
            "Get futures tick-by-tick trade data. "
            f"{_category_note} "
            "Returns: time, price, volume, side."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_futures_tick(
        symbol: str,
        category: Optional[str] = _default_category,
        count: int = 200,
    ) -> str:
        """Fetch tick-by-tick trade data for a futures symbol."""
        audit.log_tool_call("get_futures_tick", {"symbol": symbol})
        err = _validate_category(category)
        if err:
            return err
        try:
            kwargs = _build_kwargs(
                {"symbol": symbol, "category": category},
                count=str(count) if count != 200 else None,
            )
            data = extract_response_data(sdk.data.futures_market_data.get_futures_tick(**kwargs))
            return prepend_disclaimer(format_futures_tick(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_futures_tick", config.region_id)

    @mcp.tool(
        description=(
            "Get futures real-time snapshot. "
            f"{_category_note} "
            "Returns: symbol, price, change, change_ratio, volume, "
            "open_interest, settle_price, bid, ask."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_futures_snapshot(
        symbols: str,
        category: Optional[str] = _default_category,
    ) -> str:
        """Fetch real-time futures snapshot for one or more symbols."""
        audit.log_tool_call("get_futures_snapshot", {"symbols": symbols})
        err = _validate_category(category)
        if err:
            return err
        try:
            sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
            data = extract_response_data(
                sdk.data.futures_market_data.get_futures_snapshot(symbols=sym_list, category=category)
            )
            return prepend_disclaimer(format_futures_snapshot(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_futures_snapshot", config.region_id)

    @mcp.tool(
        description=(
            "Get futures order book depth. "
            f"{_category_note} "
            "Returns: symbol, bids, asks."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_futures_depth(
        symbol: str,
        category: Optional[str] = _default_category,
        depth: Optional[int] = None,
    ) -> str:
        """Fetch order book depth for a futures symbol."""
        audit.log_tool_call("get_futures_depth", {"symbol": symbol})
        err = _validate_category(category)
        if err:
            return err
        try:
            kwargs = _build_kwargs(
                {"symbol": symbol, "category": category},
                depth=depth,
            )
            data = extract_response_data(sdk.data.futures_market_data.get_futures_depth(**kwargs))
            return prepend_disclaimer(format_futures_depth(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_futures_depth", config.region_id)

    @mcp.tool(
        description=(
            "Get futures OHLCV bars in batch. "
            f"{_category_note} "
            "Returns: time, open, high, low, close, volume."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_futures_bars(
        symbols: str,
        category: Optional[str] = _default_category,
        timespan: str = "D",
        count: int = 200,
        real_time_required: bool = False,
    ) -> str:
        """Batch fetch historical OHLCV bar data for multiple futures symbols."""
        audit.log_tool_call("get_futures_bars", {"symbols": symbols})
        err = _validate_category(category)
        if err:
            return err
        try:
            sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
            kwargs = _build_kwargs(
                {"symbols": sym_list, "category": category, "timespan": timespan},
                count=str(count) if count != 200 else None,
                real_time_required=real_time_required,
            )
            data = extract_response_data(sdk.data.futures_market_data.get_futures_history_bars(**kwargs))
            return prepend_disclaimer(format_futures_bars(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_futures_bars", config.region_id)

    @mcp.tool(
        description=(
            "Get futures large order footprint (order flow). "
            f"{_category_note} "
            "Returns: time, trading_session, total, delta, buy_total, sell_total."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_futures_footprint(
        symbols: str,
        category: Optional[str] = _default_category,
        timespan: str = "M1",
        count: int = 200,
        real_time_required: bool = False,
        trading_sessions: Optional[str] = None,
    ) -> str:
        """Fetch footprint (large order) data for futures symbols."""
        audit.log_tool_call("get_futures_footprint", {"symbols": symbols})
        err = _validate_category(category)
        if err:
            return err
        try:
            sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
            kwargs = _build_kwargs(
                {"symbols": sym_list, "category": category, "timespan": timespan},
                count=str(count) if count != 200 else None,
                real_time_required=real_time_required,
                trading_sessions=trading_sessions,
            )
            data = extract_response_data(sdk.data.futures_market_data.get_futures_footprint(**kwargs))
            return prepend_disclaimer(format_futures_footprint(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_futures_footprint", config.region_id)
