"""Option market data tools for Webull MCP Server.

Provides: get_option_tick, get_option_snapshot, get_option_bars.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from webull_openapi_mcp.errors import handle_sdk_exception
from webull_openapi_mcp.formatters import (
    extract_response_data,
    prepend_disclaimer,
)

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from webull_openapi_mcp.audit import AuditLogger
    from webull_openapi_mcp.config import ServerConfig
    from webull_openapi_mcp.sdk_client import WebullSDKClient


def _format_option_tick(data) -> str:
    """Format option tick data.

    API returns: {symbol, instrument_id, result: [{time, price, volume, side}]}
    """
    if not data:
        return "No data available."
    if isinstance(data, dict):
        symbol = data.get("symbol", "N/A")
        ticks = data.get("result", [])
        lines = [f"=== Option Ticks: {symbol} ==="]
        for t in ticks:
            lines.append(
                f"  Time: {t.get('time', 'N/A')}  "
                f"Price: {t.get('price', 'N/A')}  "
                f"Volume: {t.get('volume', 'N/A')}  "
                f"Side: {t.get('side', 'N/A')}"
            )
        return "\n".join(lines)
    return str(data)


def _format_option_snapshot(data) -> str:
    """Format option snapshot data.

    API returns: [{symbol, instrument_id, price, open, high, low, pre_close, volume,
    change, change_ratio, strike_price, delta, gamma, theta, vega, rho, imp_vol,
    open_interest, bid, ask, bid_size, ask_size, deal_amount, ...}]
    """
    if not data:
        return "No data available."
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return str(data)
    lines = ["=== Option Snapshot ==="]
    for item in data:
        symbol = item.get("symbol", "N/A")
        lines.append(f"  Symbol: {symbol}")
        lines.append(
            f"    Price: {item.get('price', 'N/A')}  "
            f"Change: {item.get('change', 'N/A')}  "
            f"Change%: {item.get('change_ratio', 'N/A')}  "
            f"Volume: {item.get('volume', 'N/A')}"
        )
        lines.append(
            f"    Open: {item.get('open', 'N/A')}  "
            f"High: {item.get('high', 'N/A')}  "
            f"Low: {item.get('low', 'N/A')}  "
            f"PreClose: {item.get('pre_close', 'N/A')}"
        )
        lines.append(
            f"    Strike: {item.get('strike_price', 'N/A')}  "
            f"IV: {item.get('imp_vol', 'N/A')}  "
            f"OI: {item.get('open_interest', 'N/A')}"
        )
        lines.append(
            f"    Delta: {item.get('delta', 'N/A')}  "
            f"Gamma: {item.get('gamma', 'N/A')}  "
            f"Theta: {item.get('theta', 'N/A')}  "
            f"Vega: {item.get('vega', 'N/A')}  "
            f"Rho: {item.get('rho', 'N/A')}"
        )
        lines.append(
            f"    Bid: {item.get('bid', 'N/A')}x{item.get('bid_size', '')}  "
            f"Ask: {item.get('ask', 'N/A')}x{item.get('ask_size', '')}"
        )
    return "\n".join(lines)


def _format_option_bars(data) -> str:
    """Format option bars (OHLCV) data.

    API returns: {result: [{symbol, instrument_id, result: [{time, open, close, high, low, volume}]}]}
    """
    if not data:
        return "No data available."
    # Top-level may be {result: [...]} or directly a list
    if isinstance(data, dict):
        data = data.get("result", [data])
    if not isinstance(data, list):
        return str(data)
    lines = ["=== Option Bars ==="]
    for item in data:
        symbol = item.get("symbol", "N/A")
        bars = item.get("result", [])
        lines.append(f"  Symbol: {symbol} ({len(bars)} bars)")
        for bar in bars[:30]:
            lines.append(
                f"    Time: {bar.get('time', 'N/A')}  "
                f"O: {bar.get('open', 'N/A')}  "
                f"H: {bar.get('high', 'N/A')}  "
                f"L: {bar.get('low', 'N/A')}  "
                f"C: {bar.get('close', 'N/A')}  "
                f"V: {bar.get('volume', 'N/A')}"
            )
    return "\n".join(lines)


def register_option_market_data_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
) -> None:
    """Register option market data tools (US, HK, JP regions)."""

    @mcp.tool(
        description=(
            "Get option tick-by-tick trade data for a single option contract. "
            "Requires paid option market data subscription.\n"
            "symbol: Option symbol, e.g. AAPL260522C00300000.\n"
            "category: US_OPTION.\n"
            "count: Number of ticks, default 30, max 1200.\n"
            "Returns: time, price, volume, side (B/S/G/L/N)."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_option_tick(
        symbol: str,
        category: str = "US_OPTION",
        count: int = 30,
    ) -> str:
        """Get option tick-by-tick trade data."""
        audit.log_tool_call("get_option_tick", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.option_market_data.get_option_tick(
                    symbol=symbol, category=category, count=str(count),
                )
            )
            return prepend_disclaimer(_format_option_tick(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_option_tick", config.region_id)

    @mcp.tool(
        description=(
            "Get real-time option quote snapshots (batch, max 20 symbols). "
            "Requires paid option market data subscription.\n"
            "symbols: Comma-separated option symbols, e.g. AAPL260522C00300000,TSLA251219C00450000.\n"
            "category: US_OPTION.\n"
            "Returns: price, change, volume, open_interest, Greeks (delta/gamma/theta/vega/rho), IV, bid/ask."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_option_snapshot(
        symbols: str,
        category: str = "US_OPTION",
    ) -> str:
        """Get real-time option snapshot for one or more option symbols."""
        audit.log_tool_call("get_option_snapshot", {"symbols": symbols})
        try:
            sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
            data = extract_response_data(
                sdk.data.option_market_data.get_option_snapshot(
                    symbols=sym_list, category=category,
                )
            )
            return prepend_disclaimer(_format_option_snapshot(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_option_snapshot", config.region_id)

    @mcp.tool(
        description=(
            "Get option historical OHLCV bars (batch). "
            "Requires paid option market data subscription.\n"
            "symbols: Comma-separated option symbols.\n"
            "category: US_OPTION.\n"
            "timespan: M1, M5, M15, M30, M60, M120, M240, D, W, M, Y (default D).\n"
            "count: Number of bars, default 200, max 1200.\n"
            "Returns: time, open, high, low, close, volume per bar."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_option_bars(
        symbols: str,
        category: str = "US_OPTION",
        timespan: str = "D",
        count: int = 200,
        real_time_required: bool = False,
    ) -> str:
        """Get option historical OHLCV bar data."""
        audit.log_tool_call("get_option_bars", {"symbols": symbols, "timespan": timespan})
        try:
            sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
            kwargs: dict = {
                "symbols": sym_list,
                "category": category,
                "timespan": timespan,
                "count": str(count),
            }
            if real_time_required:
                kwargs["real_time_required"] = real_time_required
            data = extract_response_data(
                sdk.data.option_market_data.get_option_history_bars(**kwargs)
            )
            return prepend_disclaimer(_format_option_bars(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_option_bars", config.region_id)
