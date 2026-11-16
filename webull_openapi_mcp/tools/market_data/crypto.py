"""Crypto market data tools for Webull MCP Server.

Provides: get_crypto_snapshot, get_crypto_bars.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from webull_openapi_mcp.errors import handle_sdk_exception
from webull_openapi_mcp.formatters import (
    extract_response_data,
    format_crypto_bars,
    format_crypto_snapshot,
    prepend_disclaimer,
)

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from webull_openapi_mcp.audit import AuditLogger
    from webull_openapi_mcp.config import ServerConfig
    from webull_openapi_mcp.sdk_client import WebullSDKClient


def register_crypto_market_data_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
) -> None:
    """Register crypto market data tools."""

    @mcp.tool(
        description=(
            "Get cryptocurrency real-time snapshot. "
            "Returns: symbol, price, change, change_ratio, bid, ask."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_crypto_snapshot(
        symbols: str,
        category: str = "US_CRYPTO",
    ) -> str:
        """Fetch real-time crypto snapshot for one or more symbols."""
        audit.log_tool_call("get_crypto_snapshot", {"symbols": symbols})
        try:
            sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
            data = extract_response_data(
                sdk.data.crypto_market_data.get_crypto_snapshot(symbols=sym_list, category=category)
            )
            return prepend_disclaimer(format_crypto_snapshot(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_crypto_snapshot", config.region_id)

    @mcp.tool(
        description=(
            "Get cryptocurrency OHLCV bars. "
            "start_time/end_time: optional range as timestamps in milliseconds. "
            "Returns: time, open, high, low, close, volume."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_crypto_bars(
        symbols: str,
        category: str = "US_CRYPTO",
        timespan: str = "D",
        count: int = 200,
        real_time_required: bool = False,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> str:
        """Fetch historical OHLCV bar data for crypto symbols.

        Args:
            start_time: Start timestamp in milliseconds (optional).
            end_time: End timestamp in milliseconds (optional).
        """
        audit.log_tool_call("get_crypto_bars", {"symbols": symbols})
        try:
            sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
            kwargs: dict = {"symbols": sym_list, "category": category, "timespan": timespan}
            if count != 200:
                kwargs["count"] = str(count)
            if real_time_required:
                kwargs["real_time_required"] = real_time_required
            if start_time is not None:
                kwargs["start_time"] = start_time
            if end_time is not None:
                kwargs["end_time"] = end_time
            data = extract_response_data(
                sdk.data.crypto_market_data.get_crypto_history_bar(**kwargs)
            )
            return prepend_disclaimer(format_crypto_bars(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_crypto_bars", config.region_id)
