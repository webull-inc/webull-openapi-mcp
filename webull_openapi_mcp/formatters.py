"""Output formatting functions for Webull MCP Server.

Each function takes raw SDK response data (dict or list of dicts) and returns
a human-readable formatted string. The disclaimer prefix is region-aware:
- US: English only
- HK: English + Simplified Chinese + Traditional Chinese
- JP: English + Japanese
"""

from __future__ import annotations

from typing import Any

# Region-specific disclaimers
_DISCLAIMER_US = (
    "⚠️ Disclaimer: "
    "The information provided by this tool is for reference only "
    "and does not constitute investment advice. "
    "Trading involves risk; please make decisions carefully.\n\n"
)

_DISCLAIMER_HK = (
    "⚠️ Disclaimer: "
    "The information provided by this tool is for reference only "
    "and does not constitute investment advice. "
    "Trading involves risk; please make decisions carefully.\n"
    "本工具提供的信息仅供参考，不构成投资建议。交易有风险，请谨慎决策。\n"
    "本工具提供的資訊僅供參考，不構成投資建議。交易有風險，請謹慎決策。\n\n"
)

_DISCLAIMER_JP = (
    "⚠️ Disclaimer: "
    "The information provided by this tool is for reference only "
    "and does not constitute investment advice. "
    "Trading involves risk; please make decisions carefully.\n"
    "本ツールが提供する情報は参考目的のみであり、投資助言ではありません。"
    "取引にはリスクがあります。慎重に判断してください。\n\n"
)

_DISCLAIMER_SG = (
    "⚠️ Disclaimer: "
    "The information provided by this tool is for reference only "
    "and does not constitute investment advice. "
    "Trading involves risk; please make decisions carefully.\n\n"
)

_DISCLAIMER_TH = (
    "⚠️ Disclaimer: "
    "The information provided by this tool is for reference only "
    "and does not constitute investment advice. "
    "Trading involves risk; please make decisions carefully.\n\n"
)

_DISCLAIMER_MY = (
    "⚠️ Disclaimer: "
    "The information provided by this tool is for reference only "
    "and does not constitute investment advice. "
    "Trading involves risk; please make decisions carefully.\n\n"
)

_DISCLAIMER_UK = (
    "⚠️ Disclaimer: "
    "The information provided by this tool is for reference only "
    "and does not constitute investment advice. "
    "Trading involves risk; please make decisions carefully.\n\n"
)

# Default (backward compatibility)
DISCLAIMER = _DISCLAIMER_US

# Current region (set at server startup)
_current_region: str = "us"


def set_disclaimer_region(region_id: str) -> None:
    """Set the region for disclaimer output. Called once at server startup."""
    global _current_region, DISCLAIMER
    _current_region = region_id.lower()
    if _current_region == "hk":
        DISCLAIMER = _DISCLAIMER_HK
    elif _current_region == "jp":
        DISCLAIMER = _DISCLAIMER_JP
    elif _current_region == "sg":
        DISCLAIMER = _DISCLAIMER_SG
    elif _current_region == "th":
        DISCLAIMER = _DISCLAIMER_TH
    elif _current_region == "my":
        DISCLAIMER = _DISCLAIMER_MY
    elif _current_region == "uk":
        DISCLAIMER = _DISCLAIMER_UK
    else:
        DISCLAIMER = _DISCLAIMER_US

_NO_DATA = "No data available."


def prepend_disclaimer(content: str) -> str:
    """Prepend the region-appropriate disclaimer to *content*."""
    return DISCLAIMER + content


def extract_response_data(response: Any) -> Any:
    """Extract JSON data from SDK response.
    
    The Webull SDK returns requests.Response objects from most API calls.
    This helper extracts the JSON data, handling both Response objects
    and already-parsed data (for backward compatibility).
    """
    if response is None:
        return None
    # If it's a requests.Response object, extract JSON
    if hasattr(response, 'json') and callable(response.json):
        try:
            return response.json()
        except Exception:
            # If JSON parsing fails, try to get content
            if hasattr(response, 'content'):
                return response.content
            return response
    # Already parsed data (dict, list, etc.)
    return response


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get(d: dict, key: str, default: str = "N/A") -> str:
    """Safely get a value from *d*, returning *default* when missing/None."""
    val = d.get(key)
    if val is None:
        return default
    return str(val)


# ---------------------------------------------------------------------------
# Account formatters
# ---------------------------------------------------------------------------

def format_account_list(data: list[dict] | None) -> str:
    """Format account list response."""
    if not data:
        return _NO_DATA
    lines: list[str] = ["=== Account List ==="]
    for i, acct in enumerate(data, 1):
        lines.append(
            f"{i}. ID: {_get(acct, 'account_id')}  "
            f"User ID: {_get(acct, 'user_id')}  "
            f"Number: {_get(acct, 'account_number')}  "
            f"Type: {_get(acct, 'account_type')}  "
            f"Class: {_get(acct, 'account_class')}  "
            f"Label: {_get(acct, 'account_label')}"
        )
    return "\n".join(lines)


def format_account_balance(data: dict | None) -> str:
    """Format account balance response.
    
    API returns:
    - total_asset_currency, total_cash_balance, total_market_value, total_unrealized_profit_loss
    - total_net_liquidation_value (US), total_day_profit_loss (US)
    - account_currency_assets: [{currency, cash_balance, settled_cash, unsettled_cash,
      market_value, buying_power, unrealized_profit_loss, available_withdrawal, ...}]
    """
    if not data:
        return _NO_DATA
    lines: list[str] = ["=== Account Balance ==="]
    
    # Top-level summary
    lines.append(f"Currency:              {_get(data, 'total_asset_currency')}")
    lines.append(f"Total Cash Balance:    {_get(data, 'total_cash_balance')}")
    lines.append(f"Total Market Value:    {_get(data, 'total_market_value')}")
    lines.append(f"Total Unrealized P&L:  {_get(data, 'total_unrealized_profit_loss')}")
    
    # US-specific fields
    if data.get("total_net_liquidation_value"):
        lines.append(f"Net Liquidation:       {_get(data, 'total_net_liquidation_value')}")
    if data.get("total_day_profit_loss"):
        lines.append(f"Day P&L:               {_get(data, 'total_day_profit_loss')}")
    if data.get("day_trades_left"):
        lines.append(f"Day Trades Left:       {_get(data, 'day_trades_left')}")
    
    # Per-currency breakdown
    currency_assets = data.get("account_currency_assets", [])
    for asset in currency_assets:
        currency = _get(asset, "currency")
        lines.append(f"\n  --- {currency} ---")
        lines.append(f"  Cash Balance:        {_get(asset, 'cash_balance')}")
        lines.append(f"  Settled Cash:        {_get(asset, 'settled_cash')}")
        lines.append(f"  Unsettled Cash:      {_get(asset, 'unsettled_cash')}")
        lines.append(f"  Market Value:        {_get(asset, 'market_value')}")
        lines.append(f"  Buying Power:        {_get(asset, 'buying_power')}")
        lines.append(f"  Unrealized P&L:      {_get(asset, 'unrealized_profit_loss')}")
        lines.append(f"  Available Withdrawal:{_get(asset, 'available_withdrawal')}")
        # US margin fields
        if asset.get("option_buying_power"):
            lines.append(f"  Option Buying Power: {_get(asset, 'option_buying_power')}")
        if asset.get("day_buying_power"):
            lines.append(f"  Day Buying Power:    {_get(asset, 'day_buying_power')}")
    
    return "\n".join(lines)


def format_positions(data: list[dict] | None) -> str:
    """Format account positions response.
    
    API returns: [{position_id, currency, quantity, symbol, option_strategy,
    instrument_type, last_price, cost_price, unrealized_profit_loss, legs: [...]}]
    """
    if not data:
        return _NO_DATA
    lines: list[str] = ["=== Positions ==="]
    for pos in data:
        lines.append(
            f"  {_get(pos, 'symbol'):>8s}  "
            f"Qty: {_get(pos, 'quantity'):>8s}  "
            f"Type: {_get(pos, 'instrument_type'):>6s}  "
            f"Cost: {_get(pos, 'cost_price'):>10s}  "
            f"Last: {_get(pos, 'last_price'):>10s}  "
            f"Unrealized P&L: {_get(pos, 'unrealized_profit_loss'):>10s}  "
            f"Currency: {_get(pos, 'currency')}"
        )
        # Option legs
        legs = pos.get("legs", [])
        for leg in legs:
            lines.append(
                f"{'':>10s}  "
                f"Leg: {_get(leg, 'symbol')}  "
                f"Qty: {_get(leg, 'quantity')}  "
                f"Type: {_get(leg, 'option_type')}  "
                f"Strike: {_get(leg, 'option_exercise_price')}  "
                f"Exp: {_get(leg, 'option_expire_date')}"
            )
    return "\n".join(lines)


def format_position_details(data: list[dict] | dict | None) -> str:
    """Format JP account position details response."""
    if not data:
        return _NO_DATA

    if isinstance(data, dict):
        items = None
        for key in ("items", "positions", "position_details", "data"):
            if key in data:
                items = data[key]
                break
        data = [data] if items is None else items

    if not isinstance(data, list) or not data:
        return _NO_DATA

    lines: list[str] = ["=== Position Details ==="]
    for i, detail in enumerate(data, 1):
        if not isinstance(detail, dict):
            continue
        lines.append(f"\n[Position Detail {i}]")
        lines.append(
            f"  {_get(detail, 'symbol'):>8s}  "
            f"Qty: {_get(detail, 'quantity'):>8s}  "
            f"Hold: {_get(detail, 'hold_type'):>6s}  "
            f"Market Value: {_get(detail, 'market_value'):>10s}  "
            f"Currency: {_get(detail, 'currency')}"
        )
        lines.append(
            f"{'':>10s}  "
            f"Name: {_get(detail, 'symbol_name')}  "
            f"Exchange: {_get(detail, 'exchange_code')}"
        )
        lines.append(
            f"{'':>10s}  "
            f"Average Price: {_get(detail, 'average_price'):>10s}  "
            f"Unrealized P&L: {_get(detail, 'unrealized_pl'):>10s}"
        )
        lines.append(
            f"{'':>10s}  "
            f"Account Tax Type: {_get(detail, 'account_tax_type')}  "
            f"Margin Type: {_get(detail, 'margin_type')}"
        )
        lines.append(
            f"{'':>10s}  "
            f"Instrument ID: {_get(detail, 'instrument_id')}  "
            f"Contract ID: {_get(detail, 'contract_id')}  "
            f"Position ID: {_get(detail, 'id')}"
        )
        lines.append(
            f"{'':>10s}  "
            f"Base Currency: {_get(detail, 'base_currency')}  "
            f"FX Rate: {_get(detail, 'fx_rate')}  "
            f"Base Currency Market Value: {_get(detail, 'base_currency_market_value')}"
        )

    if len(lines) == 1:
        return _NO_DATA
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Stock market data formatters
# ---------------------------------------------------------------------------

def format_stock_snapshot(data: list[dict] | None) -> str:
    """Format stock snapshot response.
    
    API fields: instrument_id, pre_close, change_ratio, symbol, price, open, close,
    high, low, volume, change, ask, ask_size, bid, bid_size, last_trade_time,
    turnover, eps, eps_ttm, lot_size, bps, extend_hour_*, ovn_* fields.
    """
    if not data:
        return _NO_DATA
    lines: list[str] = ["=== Stock Snapshot ==="]
    for snap in data:
        lines.append(
            f"  {_get(snap, 'symbol'):>8s}  "
            f"Price: {_get(snap, 'price'):>10s}  "
            f"PreClose: {_get(snap, 'pre_close'):>10s}  "
            f"Change: {_get(snap, 'change'):>8s}  "
            f"Change%: {_get(snap, 'change_ratio'):>8s}"
        )
        lines.append(
            f"{'':>10s}  "
            f"Open: {_get(snap, 'open'):>10s}  "
            f"High: {_get(snap, 'high'):>10s}  "
            f"Low: {_get(snap, 'low'):>10s}  "
            f"Close: {_get(snap, 'close'):>10s}  "
            f"Vol: {_get(snap, 'volume'):>12s}"
        )
        lines.append(
            f"{'':>10s}  "
            f"Bid: {_get(snap, 'bid'):>10s} x {_get(snap, 'bid_size'):>6s}  "
            f"Ask: {_get(snap, 'ask'):>10s} x {_get(snap, 'ask_size'):>6s}"
        )
        # Fundamentals (turnover, eps, eps_ttm, lot_size, bps)
        if any(snap.get(k) for k in ("turnover", "eps", "eps_ttm", "lot_size", "bps")):
            lines.append(
                f"{'':>10s}  "
                f"Turnover: {_get(snap, 'turnover'):>12s}  "
                f"EPS: {_get(snap, 'eps'):>8s}  "
                f"EPS(TTM): {_get(snap, 'eps_ttm'):>8s}  "
                f"Lot Size: {_get(snap, 'lot_size'):>6s}  "
                f"BPS: {_get(snap, 'bps'):>8s}"
            )
        # Extended hours data
        if snap.get("extend_hour_last_price"):
            lines.append(
                f"{'':>10s}  "
                f"ExtHr Price: {_get(snap, 'extend_hour_last_price'):>10s}  "
                f"High: {_get(snap, 'extend_hour_high'):>10s}  "
                f"Low: {_get(snap, 'extend_hour_low'):>10s}  "
                f"Change: {_get(snap, 'extend_hour_change'):>8s} ({_get(snap, 'extend_hour_change_ratio')})  "
                f"Vol: {_get(snap, 'extend_hour_volume'):>12s}"
            )
        # Overnight data
        if snap.get("ovn_price"):
            lines.append(
                f"{'':>10s}  "
                f"OVN Price: {_get(snap, 'ovn_price'):>10s}  "
                f"High: {_get(snap, 'ovn_high'):>10s}  "
                f"Low: {_get(snap, 'ovn_low'):>10s}  "
                f"Change: {_get(snap, 'ovn_change'):>8s} ({_get(snap, 'ovn_change_ratio')})  "
                f"Vol: {_get(snap, 'ovn_volume'):>12s}"
            )
            lines.append(
                f"{'':>10s}  "
                f"OVN Bid: {_get(snap, 'ovn_bid'):>10s} x {_get(snap, 'ovn_bid_size'):>6s}  "
                f"OVN Ask: {_get(snap, 'ovn_ask'):>10s} x {_get(snap, 'ovn_ask_size'):>6s}"
            )
    return "\n".join(lines)


def format_stock_quotes(data: Any) -> str:
    """Format stock quotes (bid/ask depth) response.
    
    API returns single object with:
    - symbol, instrument_id, quote_time
    - asks: [{price, size, order: [{mpid, size}]}]
    - bids: [{price, size, order: [{mpid, size}]}]
    """
    if not data:
        return _NO_DATA
    
    # Handle single dict response
    if isinstance(data, dict):
        symbol = _get(data, "symbol")
        quote_time = _get(data, "quote_time")
        lines: list[str] = [f"=== Stock Quotes: {symbol} ==="]
        if quote_time != "N/A":
            lines.append(f"  Quote Time: {quote_time}")
        
        asks = data.get("asks", [])
        bids = data.get("bids", [])
        
        # Format bids (buy side)
        lines.append(f"\n  {'Bids':>10s}  {'Price':>10s}  {'Size':>10s}")
        lines.append(f"  {'----':>10s}  {'-----':>10s}  {'----':>10s}")
        for i, bid in enumerate(bids):
            lines.append(
                f"  {'L' + str(i + 1):>10s}  "
                f"{_get(bid, 'price'):>10s}  "
                f"{_get(bid, 'size'):>10s}"
            )
        
        # Format asks (sell side)
        lines.append(f"\n  {'Asks':>10s}  {'Price':>10s}  {'Size':>10s}")
        lines.append(f"  {'----':>10s}  {'-----':>10s}  {'----':>10s}")
        for i, ask in enumerate(asks):
            lines.append(
                f"  {'L' + str(i + 1):>10s}  "
                f"{_get(ask, 'price'):>10s}  "
                f"{_get(ask, 'size'):>10s}"
            )
        
        return "\n".join(lines)
    
    # Fallback for list format
    if isinstance(data, list):
        lines = ["=== Stock Quotes ==="]
        for q in data:
            if isinstance(q, dict):
                lines.append(
                    f"  {_get(q, 'symbol'):>8s}  "
                    f"Bid: {_get(q, 'bid'):>10s} x {_get(q, 'bid_size'):>6s}  "
                    f"Ask: {_get(q, 'ask'):>10s} x {_get(q, 'ask_size'):>6s}"
                )
        return "\n".join(lines)
    
    return _NO_DATA


def _format_bar_line(bar: dict, symbol_prefix: str = "") -> str:
    """Format a single OHLCV bar line."""
    return (
        f"  {symbol_prefix}"
        f"{_get(bar, 'time'):>20s}  "
        f"O: {_get(bar, 'open'):>10s}  "
        f"H: {_get(bar, 'high'):>10s}  "
        f"L: {_get(bar, 'low'):>10s}  "
        f"C: {_get(bar, 'close'):>10s}  "
        f"Vol: {_get(bar, 'volume'):>12s}"
    )


def _unwrap_bars_envelope(data: Any) -> Any:
    """Unwrap top-level {result: [...]} envelope if present."""
    if not data:
        return None
    if isinstance(data, dict) and "result" in data:
        data = data["result"]
    return data or None


def _is_grouped_bars(data: Any) -> bool:
    """Check if data is grouped bars format [{symbol, result: [bars]}]."""
    return isinstance(data, list) and bool(data) and isinstance(data[0], dict) and "result" in data[0]


def _append_grouped_bars(lines: list[str], data: list[dict]) -> None:
    """Append grouped bars (batch format) to lines."""
    for group in data:
        symbol = _get(group, "symbol")
        if symbol != "N/A":
            lines.append(f"  --- {symbol} ---")
        for bar in group.get("result", []):
            lines.append(_format_bar_line(bar))


def _append_flat_bars(lines: list[str], data: Any) -> None:
    """Append flat bars to lines."""
    for bar in (data if isinstance(data, list) else []):
        if not isinstance(bar, dict):
            continue
        prefix = f"{_get(bar, 'symbol'):>8s}  " if bar.get("symbol") else ""
        lines.append(_format_bar_line(bar, prefix))


def _format_bars_data(data: Any, title: str) -> str:
    """Shared formatter for OHLCV bar data across all asset types.

    Handles:
    - Batch envelope: {result: [{symbol, result: [bars]}]}
    - Batch unwrapped: [{symbol, result: [bars]}]
    - Flat list: [bar, bar, ...]
    """
    data = _unwrap_bars_envelope(data)
    if not data:
        return _NO_DATA

    lines: list[str] = [f"=== {title} ==="]

    if _is_grouped_bars(data):
        _append_grouped_bars(lines, data)
    else:
        _append_flat_bars(lines, data)

    return "\n".join(lines)


def format_stock_bars(data: Any) -> str:
    """Format stock OHLCV bar data.

    Handles multiple response formats:
    - Batch bar API envelope: {result: [{symbol, instrument_id, result: [{time, open, ...}]}]}
    - Batch bar API unwrapped: [{symbol, instrument_id, result: [{time, open, ...}]}]
    - Single bar API: list of {tickerId, symbol, time, open, close, high, low, volume}
    """
    return _format_bars_data(data, "Stock Bars (OHLCV)")


def format_stock_tick(data: Any) -> str:
    """Format stock tick-by-tick data.
    
    API returns: {symbol, instrument_id, result: [{time, price, volume, side, trading_session}]}
    """
    if not data:
        return _NO_DATA
    
    # Handle nested structure
    if isinstance(data, dict):
        symbol = _get(data, "symbol")
        ticks = data.get("result", [])
        lines: list[str] = [f"=== Stock Ticks: {symbol} ==="]
        for tick in ticks:
            lines.append(
                f"  {_get(tick, 'time'):>20s}  "
                f"Price: {_get(tick, 'price'):>10s}  "
                f"Vol: {_get(tick, 'volume'):>10s}  "
                f"Side: {_get(tick, 'side'):>4s}  "
                f"Session: {_get(tick, 'trading_session')}"
            )
        return "\n".join(lines)
    
    # Fallback for flat list
    lines = ["=== Stock Ticks ==="]
    for tick in data:
        lines.append(
            f"  {_get(tick, 'time'):>20s}  "
            f"Price: {_get(tick, 'price'):>10s}  "
            f"Vol: {_get(tick, 'volume'):>10s}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Crypto market data formatters
# ---------------------------------------------------------------------------

def format_crypto_snapshot(data: Any) -> str:
    """Format crypto snapshot response.

    API returns flat list: [{instrument_id, symbol, pre_close, last_trade_time,
    price, open, high, low, change, change_ratio, quote_time, bid, bid_size,
    ask, ask_size}]
    """
    if not data:
        return _NO_DATA
    if isinstance(data, dict):
        data = [data]
    lines: list[str] = ["=== Crypto Snapshot ==="]
    for snap in data:
        lines.append(
            f"  {_get(snap, 'symbol'):>10s}  "
            f"Price: {_get(snap, 'price'):>12s}  "
            f"Change: {_get(snap, 'change'):>10s}  "
            f"Change%: {_get(snap, 'change_ratio'):>8s}"
        )
        lines.append(
            f"{'':>12s}  "
            f"Open: {_get(snap, 'open'):>12s}  "
            f"High: {_get(snap, 'high'):>12s}  "
            f"Low: {_get(snap, 'low'):>12s}  "
            f"PreClose: {_get(snap, 'pre_close'):>12s}"
        )
        lines.append(
            f"{'':>12s}  "
            f"Bid: {_get(snap, 'bid'):>12s} x {_get(snap, 'bid_size'):>8s}  "
            f"Ask: {_get(snap, 'ask'):>12s} x {_get(snap, 'ask_size'):>8s}"
        )
    return "\n".join(lines)


def format_crypto_bars(data: Any) -> str:
    """Format crypto OHLCV bar data.

    Handles nested result structure like stock batch bars:
    [{symbol, instrument_id, result: [{time, open, close, high, low, volume}]}]
    """
    return _format_bars_data(data, "Crypto Bars (OHLCV)")


# ---------------------------------------------------------------------------
# Order formatters
# ---------------------------------------------------------------------------

def _format_order_detail(detail: dict) -> list[str]:
    """Format the core fields of a single order detail."""
    return [
        f"    Client Order ID:    {_get(detail, 'client_order_id')}",
        f"    Order ID:           {_get(detail, 'order_id')}",
        f"    Symbol:             {_get(detail, 'symbol')}",
        f"    Side:               {_get(detail, 'side')}",
        f"    Status:             {_get(detail, 'status')}",
        f"    Order Type:         {_get(detail, 'order_type')}",
        f"    Instrument Type:    {_get(detail, 'instrument_type')}",
        f"    Total Quantity:     {_get(detail, 'total_quantity')}",
        f"    Filled Quantity:    {_get(detail, 'filled_quantity')}",
        f"    Limit Price:        {_get(detail, 'limit_price')}",
        f"    Stop Price:         {_get(detail, 'stop_price')}",
        f"    Filled Price:       {_get(detail, 'filled_price')}",
        f"    Time In Force:      {_get(detail, 'time_in_force')}",
        f"    Trading Session:    {_get(detail, 'support_trading_session')}",
        f"    Place Time:         {_get(detail, 'place_time_at')}",
        f"    Place Timestamp:    {_get(detail, 'place_time')}",
        f"    Filled Time:        {_get(detail, 'filled_time_at')}",
        f"    Filled Timestamp:   {_get(detail, 'filled_time')}",
    ]


def _format_order_extra_fields(detail: dict) -> list[str]:
    """Format optional trailing, algo, event, and position_intent fields."""
    lines: list[str] = []

    # JP order fields
    if detail.get("account_tax_type"):
        lines.append(f"    Account Tax Type:  {_get(detail, 'account_tax_type')}")
    if detail.get("margin_type"):
        lines.append(f"    Margin Type:       {_get(detail, 'margin_type')}")
    close_contracts = detail.get("close_contracts") or []
    if isinstance(close_contracts, list) and close_contracts:
        lines.append("    Close Contracts:")
        for contract in close_contracts:
            if not isinstance(contract, dict):
                continue
            lines.append(
                f"      Contract ID: {_get(contract, 'contract_id')}  "
                f"Qty: {_get(contract, 'quantity')}"
            )

    # Trailing stop fields
    if detail.get("trailing_type"):
        lines.append(f"    Trailing Type:      {_get(detail, 'trailing_type')}")
        lines.append(f"    Trailing Step:      {_get(detail, 'trailing_stop_step')}")

    # Algo order fields
    if detail.get("algo_type"):
        lines.append(f"    Algo Type:          {_get(detail, 'algo_type')}")
        if detail.get("algo_start_time"):
            lines.append(f"    Algo Start Time:    {_get(detail, 'algo_start_time')}")
        if detail.get("algo_end_time"):
            lines.append(f"    Algo End Time:      {_get(detail, 'algo_end_time')}")
        if detail.get("target_vol_percent"):
            lines.append(f"    Target Vol %:       {_get(detail, 'target_vol_percent')}")
        if detail.get("max_target_percent"):
            lines.append(f"    Max Target %:       {_get(detail, 'max_target_percent')}")

    # Event order fields
    if detail.get("event_outcome"):
        lines.append(f"    Event Outcome:      {_get(detail, 'event_outcome')}")

    # Option position intent
    if detail.get("position_intent"):
        lines.append(f"    Position Intent:    {_get(detail, 'position_intent')}")

    return lines


def _format_option_legs(legs: list[dict]) -> list[str]:
    """Format option legs for an order detail."""
    lines: list[str] = ["\n    [Option Legs]"]
    for j, leg in enumerate(legs, 1):
        lines.append(f"      Leg {j}:")
        lines.append(f"        Symbol:             {_get(leg, 'symbol')}")
        lines.append(f"        Side:               {_get(leg, 'side')}")
        lines.append(f"        Quantity:           {_get(leg, 'quantity')}")
        lines.append(f"        Option Type:        {_get(leg, 'option_type')}")
        lines.append(f"        Option Category:    {_get(leg, 'option_category')}")
        lines.append(f"        Option Strategy:    {_get(leg, 'option_strategy')}")
        lines.append(f"        Strike Price:       {_get(leg, 'strike_price')}")
        lines.append(f"        Expire Date:        {_get(leg, 'option_expire_date')}")
        lines.append(f"        Multiplier:         {_get(leg, 'option_contract_multiplier')}")
        lines.append(f"        Deliverable:        {_get(leg, 'option_contract_deliverable')}")
    return lines


def _format_order_item(data: dict) -> list[str]:
    """Format a single order item (used by history, open orders, and detail).
    
    Structure:
    {
        "client_order_id": "...",
        "combo_type": "NORMAL",
        "orders": [
            {
                "client_order_id": "...",
                "order_id": "...",
                "symbol": "...",
                ...
                "legs": [...]
            }
        ]
    }
    """
    lines: list[str] = [
        f"Client Order ID:  {_get(data, 'client_order_id')}",
        f"Combo Type:       {_get(data, 'combo_type')}",
    ]

    orders = data.get("orders", [])
    if not orders or not isinstance(orders, list):
        lines.append("\n  No order details available.")
        return lines

    for i, detail in enumerate(orders):
        header = f"\n  --- Order {i + 1} ---" if len(orders) > 1 else "\n  [Order Details]"
        lines.append(header)
        lines.extend(_format_order_detail(detail))
        lines.extend(_format_order_extra_fields(detail))
        legs = detail.get("legs") or []
        if legs:
            lines.extend(_format_option_legs(legs))

    return lines


def format_order_preview(data: dict | None) -> str:
    """Format order preview response.
    
    API may return fields like: estimated_cost, estimated_transaction_fee,
    estimated_commission, estimated_exchange_fee, etc.
    """
    if not data:
        return _NO_DATA
    lines: list[str] = ["=== Order Preview ==="]
    for key, value in data.items():
        label = key.replace("_", " ").title()
        lines.append(f"  {label}: {value}")
    return "\n".join(lines)


def format_order_history(data: list[dict] | None) -> str:
    """Format order history response."""
    if not data:
        return _NO_DATA
    lines: list[str] = ["=== Order History ==="]
    for i, order in enumerate(data, 1):
        lines.append(f"\n[Order Entry {i}]")
        lines.extend(_format_order_item(order))
    return "\n".join(lines)


def format_open_orders(data: list[dict] | None) -> str:
    """Format open orders response."""
    if not data:
        return _NO_DATA
    lines: list[str] = ["=== Open Orders ==="]
    for i, order in enumerate(data, 1):
        lines.append(f"\n[Order Entry {i}]")
        lines.extend(_format_order_item(order))
    return "\n".join(lines)


def format_order_detail(data: dict | None) -> str:
    """Format single order detail response."""
    if not data:
        return _NO_DATA
    lines: list[str] = ["=== Order Detail ==="]
    lines.extend(_format_order_item(data))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Instrument formatters
# ---------------------------------------------------------------------------

def _format_flat_item(item: dict, indent: str = "  ") -> list[str]:
    """Format a single dict item as flat key-value lines."""
    lines: list[str] = []
    for key, value in item.items():
        if isinstance(value, (dict, list)):
            continue  # Skip nested structures
        lines.append(f"{indent}{key}: {value}")
    return lines


def _format_flat_list(data: Any, title: str) -> str:
    """Format a list of dicts as flat key-value output."""
    if not data:
        return _NO_DATA
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return _NO_DATA
    lines: list[str] = [f"=== {title} ==="]
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        if i > 0:
            lines.append("")
        lines.extend(_format_flat_item(item))
    return "\n".join(lines)


def format_instruments(data: Any) -> str:
    """Format stock/ETF instrument list response."""
    return _format_flat_list(data, "Instruments")


# ---------------------------------------------------------------------------
# Preview / Place order result formatters
# ---------------------------------------------------------------------------

def format_preview_order(data: dict | None) -> str:
    """Format order preview response."""
    if not data:
        return _NO_DATA
    lines: list[str] = [
        "=== Order Preview ===",
        f"Symbol:          {_get(data, 'symbol')}",
        f"Side:            {_get(data, 'side')}",
        f"Quantity:        {_get(data, 'quantity')}",
        f"Order Type:      {_get(data, 'order_type')}",
        f"Price:           {_get(data, 'price')}",
        f"Est. Total Cost: {_get(data, 'total_cost')}",
        f"Est. Commission: {_get(data, 'commission')}",
        f"Est. Fees:       {_get(data, 'fees')}",
    ]
    return "\n".join(lines)


def format_preview_option_order(data: dict | None) -> str:
    """Format option order preview response."""
    if not data:
        return _NO_DATA
    lines: list[str] = [
        "=== Option Order Preview ===",
        f"Strategy:        {_get(data, 'strategy')}",
        f"Order Type:      {_get(data, 'order_type')}",
        f"Est. Total Cost: {_get(data, 'total_cost')}",
        f"Est. Commission: {_get(data, 'commission')}",
        f"Est. Fees:       {_get(data, 'fees')}",
    ]
    legs = data.get("legs") or []
    if legs:
        lines.append("  Legs:")
        for j, leg in enumerate(legs, 1):
            lines.append(
                f"    {j}. {_get(leg, 'symbol')}  "
                f"{_get(leg, 'side')}  "
                f"Qty: {_get(leg, 'quantity')}  "
                f"{_get(leg, 'option_type')}  "
                f"Strike: {_get(leg, 'strike_price')}  "
                f"Exp: {_get(leg, 'option_expire_date')}"
            )
    return "\n".join(lines)


def format_place_order_result(data: dict | None) -> str:
    """Format place-order result response."""
    if not data:
        return _NO_DATA
    lines: list[str] = [
        "=== Place Order Result ===",
        f"Client Order ID: {_get(data, 'client_order_id')}",
        f"Status:          {_get(data, 'status')}",
    ]
    return "\n".join(lines)


def format_place_option_order_result(data: dict | None) -> str:
    """Format place-option-order result response."""
    if not data:
        return _NO_DATA
    lines: list[str] = [
        "=== Place Option Order Result ===",
        f"Client Order ID: {_get(data, 'client_order_id')}",
        f"Status:          {_get(data, 'status')}",
    ]
    return "\n".join(lines)


def format_replace_order_result(data: dict | None) -> str:
    """Format replace-order result response."""
    if not data:
        return _NO_DATA
    lines: list[str] = [
        "=== Replace Order Result ===",
        f"Client Order ID: {_get(data, 'client_order_id')}",
        f"Status:          {_get(data, 'status')}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Futures market data formatters
# ---------------------------------------------------------------------------

def format_futures_tick(data: Any) -> str:
    """Format futures tick-by-tick data.

    API returns: {symbol, instrument_id, result: [{time, price, volume, side}]}
    """
    if not data:
        return _NO_DATA

    # Handle nested structure
    if isinstance(data, dict):
        symbol = _get(data, "symbol")
        ticks = data.get("result", [])
        lines: list[str] = [f"=== Futures Ticks: {symbol} ==="]
        for tick in ticks:
            lines.append(
                f"  {_get(tick, 'time'):>20s}  "
                f"Price: {_get(tick, 'price'):>10s}  "
                f"Vol: {_get(tick, 'volume'):>10s}  "
                f"Side: {_get(tick, 'side'):>4s}"
            )
        return "\n".join(lines)

    # Fallback for flat list
    lines = ["=== Futures Ticks ==="]
    for tick in data:
        lines.append(
            f"  {_get(tick, 'time'):>20s}  "
            f"Price: {_get(tick, 'price'):>10s}  "
            f"Vol: {_get(tick, 'volume'):>10s}"
        )
    return "\n".join(lines)


def format_futures_snapshot(data: Any) -> str:
    """Format futures snapshot response.

    API returns flat list: [{symbol, instrument_id, price, open, high, low,
    pre_close, volume, change, change_ratio, open_interest, settle_price,
    settle_date, bid, ask, bid_size, ask_size, ...}]
    """
    if not data:
        return _NO_DATA
    if isinstance(data, dict):
        data = [data]
    lines: list[str] = ["=== Futures Snapshot ==="]
    for snap in data:
        lines.append(
            f"  {_get(snap, 'symbol'):>12s}  "
            f"Price: {_get(snap, 'price'):>10s}  "
            f"Change: {_get(snap, 'change'):>8s}  "
            f"Change%: {_get(snap, 'change_ratio'):>8s}  "
            f"Volume: {_get(snap, 'volume'):>12s}  "
            f"Open Int: {_get(snap, 'open_interest'):>10s}"
        )
        lines.append(
            f"{'':>14s}  "
            f"Open: {_get(snap, 'open'):>10s}  "
            f"High: {_get(snap, 'high'):>10s}  "
            f"Low: {_get(snap, 'low'):>10s}  "
            f"PreClose: {_get(snap, 'pre_close'):>10s}"
        )
        lines.append(
            f"{'':>14s}  "
            f"Bid: {_get(snap, 'bid'):>10s} x {_get(snap, 'bid_size'):>6s}  "
            f"Ask: {_get(snap, 'ask'):>10s} x {_get(snap, 'ask_size'):>6s}  "
            f"Settle: {_get(snap, 'settle_price'):>10s} ({_get(snap, 'settle_date')})"
        )
    return "\n".join(lines)


def format_futures_depth(data: Any) -> str:
    """Format futures order book depth response.

    API returns: {symbol, instrument_id, asks: [{price, size}], bids: [{price, size}]}
    """
    if not data:
        return _NO_DATA
    if not isinstance(data, dict):
        return _NO_DATA
    lines: list[str] = ["=== Futures Depth ==="]
    lines.append(f"Symbol: {_get(data, 'symbol')}")
    bids = data.get("bids") or []
    asks = data.get("asks") or []
    lines.append("  Bids:")
    for bid in bids:
        lines.append(f"    {_get(bid, 'price'):>10s} x {_get(bid, 'size'):>8s}")
    lines.append("  Asks:")
    for ask in asks:
        lines.append(f"    {_get(ask, 'price'):>10s} x {_get(ask, 'size'):>8s}")
    return "\n".join(lines)


def format_futures_bars(data: Any) -> str:
    """Format futures OHLCV bar data.

    Handles nested result structure:
    {result: [{symbol, instrument_id, result: [{time, open, close, high, low, volume}]}]}
    or list of symbol groups: [{symbol, instrument_id, result: [...]}]
    """
    return _format_bars_data(data, "Futures Bars (OHLCV)")


def format_futures_footprint(data: Any) -> str:
    """Format futures footprint (large order) data.

    API returns same nested structure as stock footprint:
    {symbol, instrument_id, result: [{time, trading_session, total, delta,
    buy_total, sell_total, buy_detail, sell_detail}]}
    """
    if not data:
        return _NO_DATA

    if isinstance(data, dict):
        data = [data]

    lines: list[str] = ["=== Futures Footprint ==="]
    for group in data:
        if isinstance(group, dict) and "result" in group:
            symbol = _get(group, "symbol")
            if symbol != "N/A":
                lines.append(f"  --- {symbol} ---")
            for fp in group.get("result", []):
                lines.append(
                    f"  {_get(fp, 'time'):>20s}  "
                    f"Session: {_get(fp, 'trading_session'):>4s}  "
                    f"Total: {_get(fp, 'total'):>10s}  "
                    f"Delta: {_get(fp, 'delta'):>10s}  "
                    f"Buy: {_get(fp, 'buy_total'):>10s}  "
                    f"Sell: {_get(fp, 'sell_total'):>10s}"
                )
        else:
            lines.append(
                f"  {_get(group, 'time'):>20s}  "
                f"Total: {_get(group, 'total'):>10s}  "
                f"Delta: {_get(group, 'delta'):>10s}"
            )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Event contract market data formatters
# ---------------------------------------------------------------------------

def format_event_tick(data: Any) -> str:
    """Format event contract tick-by-tick data.

    API returns: {symbol, instrument_id, result: [{time, price, volume, side}]}
    """
    if not data:
        return _NO_DATA

    # Handle nested structure
    if isinstance(data, dict):
        symbol = _get(data, "symbol")
        ticks = data.get("result", [])
        lines: list[str] = [f"=== Event Ticks: {symbol} ==="]
        for tick in ticks:
            lines.append(
                f"  {_get(tick, 'time'):>20s}  "
                f"Price: {_get(tick, 'price'):>10s}  "
                f"Vol: {_get(tick, 'volume'):>10s}  "
                f"Side: {_get(tick, 'side'):>4s}"
            )
        return "\n".join(lines)

    # Fallback for flat list
    lines = ["=== Event Ticks ==="]
    for tick in data:
        lines.append(
            f"  {_get(tick, 'time'):>20s}  "
            f"Price: {_get(tick, 'price'):>10s}  "
            f"Vol: {_get(tick, 'volume'):>10s}"
        )
    return "\n".join(lines)


def format_event_snapshot(data: Any) -> str:
    """Format event contract snapshot response.

    API returns flat list similar to stock snapshot with fields:
    symbol, instrument_id, price, open, high, low, pre_close, volume,
    change, change_ratio, bid, bid_size, ask, ask_size, etc.
    """
    if not data:
        return _NO_DATA
    if isinstance(data, dict):
        data = [data]
    lines: list[str] = ["=== Event Snapshot ==="]
    for snap in data:
        lines.append(
            f"  {_get(snap, 'symbol'):>15s}  "
            f"Price: {_get(snap, 'price'):>6s}  "
            f"Change: {_get(snap, 'change'):>8s}  "
            f"Change%: {_get(snap, 'change_ratio'):>8s}  "
            f"Volume: {_get(snap, 'volume'):>10s}"
        )
        lines.append(
            f"{'':>17s}  "
            f"Bid: {_get(snap, 'bid'):>6s} x {_get(snap, 'bid_size'):>6s}  "
            f"Ask: {_get(snap, 'ask'):>6s} x {_get(snap, 'ask_size'):>6s}"
        )
    return "\n".join(lines)


def format_event_depth(data: Any) -> str:
    """Format event contract order book depth.

    API returns: {symbol, instrument_id, asks: [{price, size}], bids: [{price, size}]}
    """
    if not data:
        return _NO_DATA
    if not isinstance(data, dict):
        return _NO_DATA
    lines: list[str] = ["=== Event Depth ==="]
    lines.append(f"Symbol: {_get(data, 'symbol')}")
    bids = data.get("bids") or []
    asks = data.get("asks") or []
    lines.append("  Bids:")
    for bid in bids:
        lines.append(f"    {_get(bid, 'price'):>6s} x {_get(bid, 'size'):>8s}")
    lines.append("  Asks:")
    for ask in asks:
        lines.append(f"    {_get(ask, 'price'):>6s} x {_get(ask, 'size'):>8s}")
    return "\n".join(lines)


def format_event_bars(data: Any) -> str:
    """Format event contract OHLCV bar data.

    Handles nested result structure like stock batch bars:
    [{symbol, instrument_id, result: [{time, open, close, high, low, volume}]}]
    """
    return _format_bars_data(data, "Event Bars (OHLCV)")


# ---------------------------------------------------------------------------
# Stock footprint formatter
# ---------------------------------------------------------------------------

def format_stock_footprint(data: Any) -> str:
    """Format stock footprint (large order) data.
    
    API returns: {symbol, instrument_id, result: [{time, trading_session, total, delta,
    buy_total, sell_total, buy_detail: {price: qty}, sell_detail: {price: qty}}]}
    """
    if not data:
        return _NO_DATA
    
    # Handle nested structure (single or list of symbols)
    if isinstance(data, dict):
        data = [data]
    
    lines: list[str] = ["=== Stock Footprint ==="]
    for group in data:
        if isinstance(group, dict) and "result" in group:
            symbol = _get(group, "symbol")
            if symbol != "N/A":
                lines.append(f"  --- {symbol} ---")
            for fp in group.get("result", []):
                lines.append(
                    f"  {_get(fp, 'time'):>20s}  "
                    f"Session: {_get(fp, 'trading_session'):>4s}  "
                    f"Total: {_get(fp, 'total'):>10s}  "
                    f"Delta: {_get(fp, 'delta'):>10s}  "
                    f"Buy: {_get(fp, 'buy_total'):>10s}  "
                    f"Sell: {_get(fp, 'sell_total'):>10s}"
                )
        else:
            # Fallback for flat format
            lines.append(
                f"  {_get(group, 'time'):>20s}  "
                f"Total: {_get(group, 'total'):>10s}  "
                f"Delta: {_get(group, 'delta'):>10s}"
            )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trading instrument formatters
# ---------------------------------------------------------------------------

def format_futures_products(data: Any) -> str:
    """Format futures products list."""
    return _format_flat_list(data, "Futures Products")


def format_futures_product_classes(data: Any) -> str:
    """Format futures product classes list."""
    return _format_flat_list(data, "Futures Product Classes")


def format_event_series(data: Any) -> str:
    """Format event series list."""
    return _format_flat_list(data, "Event Series")


def format_event_categories(data: Any) -> str:
    """Format event categories list."""
    return _format_flat_list(data, "Event Categories")


def format_event_events(data: Any) -> str:
    """Format event events list."""
    return _format_flat_list(data, "Event Events")


# ---------------------------------------------------------------------------
# Screener formatters
# ---------------------------------------------------------------------------

def _format_screener_item(item: dict) -> str:
    """Format a single screener result item."""
    lines = [
        f"  {_get(item, 'symbol')} - {_get(item, 'name')}  (instrument_id: {_get(item, 'instrument_id')})",
        f"    Price: {_get(item, 'price')}  Pre Close: {_get(item, 'pre_close')}  Open: {_get(item, 'open')}  High: {_get(item, 'high')}  Low: {_get(item, 'low')}  Close: {_get(item, 'close')}",
        f"    Change: {_get(item, 'change')}  Change Ratio: {_get(item, 'change_ratio')}  Amplitude: {_get(item, 'amplitude')}",
        f"    Volume: {_get(item, 'volume')}  Turnover: {_get(item, 'turnover')}  Turnover Rate: {_get(item, 'turnover_rate')}  Market Value: {_get(item, 'market_value')}",
        f"    Exchange: {_get(item, 'exchange_code')}  Currency: {_get(item, 'currency_code')}",
    ]
    return "\n".join(lines)


def format_gainers_losers(data: Any) -> str:
    """Format gainers/losers screener response.

    API returns: {hasMore: bool, data: [{instrumentId, symbol, name, price,
    change, changePercent, volume, marketValue, ...}]}
    """
    if not data:
        return _NO_DATA

    items = data.get("data", []) if isinstance(data, dict) else data
    if not items:
        return _NO_DATA

    lines: list[str] = ["=== Gainers / Losers ==="]
    for item in items:
        if isinstance(item, dict):
            lines.append(_format_screener_item(item))

    has_more = data.get("has_more") if isinstance(data, dict) else None
    if has_more is True:
        lines.append("\n  (More results available — increase page_size or page_index)")

    return "\n".join(lines)


def format_most_active(data: Any) -> str:
    """Format most active screener response.

    API returns: {hasMore: bool, data: [{instrumentId, symbol, name, price,
    change, changePercent, volume, marketValue, relativeVolume10d, ...}]}
    """
    if not data:
        return _NO_DATA

    items = data.get("data", []) if isinstance(data, dict) else data
    if not items:
        return _NO_DATA

    lines: list[str] = ["=== Most Active ==="]
    for item in items:
        if isinstance(item, dict):
            rel_vol = _get(item, "relative_volume_10d")
            extra = f"\n    Relative Volume 10d: {rel_vol}" if rel_vol != "N/A" else ""
            lines.append(_format_screener_item(item) + extra)

    has_more = data.get("has_more") if isinstance(data, dict) else None
    if has_more is True:
        lines.append("\n  (More results available — increase page_size or page_index)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Watchlist formatters
# ---------------------------------------------------------------------------

def format_watchlist(data: Any) -> str:
    """Format watchlist list response.

    API returns list: [{watchlist_id, name, sort, create_time, update_time}]
    """
    if not data:
        return _NO_DATA

    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return _NO_DATA

    lines: list[str] = ["=== Watchlists ==="]
    for i, wl in enumerate(data, 1):
        if not isinstance(wl, dict):
            continue
        lines.append(
            f"  {i}. {_get(wl, 'name'):<20s}  "
            f"ID: {_get(wl, 'watchlist_id')}  "
            f"Sort: {_get(wl, 'sort')}  "
            f"Created: {_get(wl, 'create_time')}  "
            f"Updated: {_get(wl, 'update_time')}"
        )

    return "\n".join(lines)


def format_watchlist_instruments(data: Any) -> str:
    """Format watchlist instruments response.

    API returns: {watchlist_id, instruments: [{instrument_id, symbol, name,
    exchange_code, sort, added_time}]}
    """
    if not data:
        return _NO_DATA

    instruments = data.get("instruments", []) if isinstance(data, dict) else data
    if not instruments:
        wid = data.get("watchlist_id", "") if isinstance(data, dict) else ""
        return f"=== Watchlist Instruments (ID: {wid}) ===\n  No instruments in this watchlist."

    wid = data.get("watchlist_id", "") if isinstance(data, dict) else ""
    lines: list[str] = [f"=== Watchlist Instruments (ID: {wid}) ==="]
    for i, inst in enumerate(instruments, 1):
        if not isinstance(inst, dict):
            continue
        lines.append(
            f"  {i}. {_get(inst, 'symbol'):>8s}  "
            f"{_get(inst, 'name'):<20s}  "
            f"ID: {_get(inst, 'instrument_id')}  "
            f"Exchange: {_get(inst, 'exchange_code')}  "
            f"Sort: {_get(inst, 'sort')}  "
            f"Added: {_get(inst, 'added_time')}"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Fundamental data formatters
# ---------------------------------------------------------------------------

def format_company_profile(data: Any) -> str:
    """Format company profile response.

    API returns: {symbol, category, company_name, establish_date, exhibition_code,
    profile, employees, address, ceo, industries}
    """
    if not data:
        return _NO_DATA
    if not isinstance(data, dict):
        return _NO_DATA

    lines: list[str] = [f"=== Company Profile: {_get(data, 'symbol')} ==="]
    lines.append(f"  Category:        {_get(data, 'category')}")
    lines.append(f"  Company Name:    {_get(data, 'company_name')}")
    lines.append(f"  Exchange:        {_get(data, 'exhibition_code')}")
    lines.append(f"  CEO:             {_get(data, 'ceo')}")
    lines.append(f"  Employees:       {_get(data, 'employees')}")
    lines.append(f"  Established:     {_get(data, 'establish_date')}")
    lines.append(f"  Address:         {_get(data, 'address')}")

    industries = data.get("industries")
    if industries:
        if isinstance(industries, list):
            lines.append(f"  Industries:      {', '.join(industries)}")
        else:
            lines.append(f"  Industries:      {industries}")

    profile = data.get("profile")
    if profile:
        lines.append(f"\n  Description:\n    {profile}")

    return "\n".join(lines)


def format_analyst_rating(data: Any) -> str:
    """Format analyst rating response.

    API returns: {symbol, category, number, under_perform, buy, sell,
    strong_buy, hold, effective_start_date}
    """
    if not data:
        return _NO_DATA
    if not isinstance(data, dict):
        return _NO_DATA

    lines: list[str] = [f"=== Analyst Rating: {_get(data, 'symbol')} ==="]
    lines.append(f"  Category:        {_get(data, 'category')}")
    lines.append(f"  Total Analysts:  {_get(data, 'number')}")
    lines.append(f"  Strong Buy:      {_get(data, 'strong_buy')}")
    lines.append(f"  Buy:             {_get(data, 'buy')}")
    lines.append(f"  Hold:            {_get(data, 'hold')}")
    lines.append(f"  Sell:            {_get(data, 'sell')}")
    lines.append(f"  Under Perform:   {_get(data, 'under_perform')}")
    lines.append(f"  Effective Since: {_get(data, 'effective_start_date')}")

    return "\n".join(lines)


def format_analyst_target_price(data: Any) -> str:
    """Format analyst target price response.

    API returns: {symbol, category, mean, low, high, median, currency,
    effective_start_date}
    """
    if not data:
        return _NO_DATA
    if not isinstance(data, dict):
        return _NO_DATA

    lines: list[str] = [f"=== Analyst Target Price: {_get(data, 'symbol')} ==="]
    lines.append(f"  Category:        {_get(data, 'category')}")
    lines.append(f"  Mean:            {_get(data, 'mean')}")
    lines.append(f"  Median:          {_get(data, 'median')}")
    lines.append(f"  High:            {_get(data, 'high')}")
    lines.append(f"  Low:             {_get(data, 'low')}")
    lines.append(f"  Currency:        {_get(data, 'currency')}")
    lines.append(f"  Effective Since: {_get(data, 'effective_start_date')}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# NOII formatters
# ---------------------------------------------------------------------------

def format_noii_bars(data: Any) -> str:
    """Format NOII K-line bars response.

    API returns list: [{instrument_id, symbol, imbalance_time, imbalance_ref_price,
    imbalance_near_price, imbalance_far_price, imbalance_action_type}]
    """
    if not data:
        return _NO_DATA

    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return _NO_DATA

    lines: list[str] = ["=== NOII Bars ==="]
    for bar in data:
        if not isinstance(bar, dict):
            continue
        lines.append(
            f"  {_get(bar, 'symbol'):>8s}  "
            f"ID: {_get(bar, 'instrument_id')}  "
            f"Time: {_get(bar, 'imbalance_time')}  "
            f"Ref: {_get(bar, 'imbalance_ref_price'):>10s}  "
            f"Near: {_get(bar, 'imbalance_near_price'):>10s}  "
            f"Far: {_get(bar, 'imbalance_far_price'):>10s}  "
            f"Type: {_get(bar, 'imbalance_action_type')}"
        )

    return "\n".join(lines)


def format_noii_snapshot(data: Any) -> str:
    """Format NOII snapshot response.

    API returns: {instrument_id, symbol, paired_shares, imbalance_shares,
    imbalance_side, imbalance_ref_price, imbalance_near_price, imbalance_far_price,
    imbalance_action_type, imbalance_time, imbalance_var_indicator}
    """
    if not data:
        return _NO_DATA

    if isinstance(data, list):
        data = data[0] if data else None
    if not data or not isinstance(data, dict):
        return _NO_DATA

    lines: list[str] = [f"=== NOII Snapshot: {_get(data, 'symbol')} ==="]
    lines.append(f"  Instrument ID:   {_get(data, 'instrument_id')}")
    lines.append(f"  Action Type:     {_get(data, 'imbalance_action_type')}")
    lines.append(f"  Time:            {_get(data, 'imbalance_time')}")
    lines.append(f"  Paired Shares:   {_get(data, 'paired_shares')}")
    lines.append(f"  Imbalance Shares:{_get(data, 'imbalance_shares')}")
    lines.append(f"  Imbalance Side:  {_get(data, 'imbalance_side')}")
    lines.append(f"  Ref Price:       {_get(data, 'imbalance_ref_price')}")
    lines.append(f"  Near Price:      {_get(data, 'imbalance_near_price')}")
    lines.append(f"  Far Price:       {_get(data, 'imbalance_far_price')}")
    lines.append(f"  Var Indicator:   {_get(data, 'imbalance_var_indicator')}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Stock fundamentals formatters
# ---------------------------------------------------------------------------

def format_capital_flow(data: Any) -> str:
    """Format stock capital flow response.

    API returns list: [{date, large_in, large_out, medium_in, medium_out,
    small_in, small_out}]
    """
    if not data:
        return _NO_DATA
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return _NO_DATA

    lines: list[str] = ["=== Capital Flow ==="]
    for item in data:
        if not isinstance(item, dict):
            continue
        lines.append(f"  Date: {_get(item, 'date')}")
        lines.append(
            f"    Large:  In {_get(item, 'large_in'):>14s}  Out {_get(item, 'large_out'):>14s}"
        )
        lines.append(
            f"    Medium: In {_get(item, 'medium_in'):>14s}  Out {_get(item, 'medium_out'):>14s}"
        )
        lines.append(
            f"    Small:  In {_get(item, 'small_in'):>14s}  Out {_get(item, 'small_out'):>14s}"
        )
    return "\n".join(lines)


def format_sec_filings(data: Any) -> str:
    """Format SEC filings response.

    API returns: {symbol, category, filings: [{title, url, publish_date}]}
    """
    if not data:
        return _NO_DATA
    if not isinstance(data, dict):
        return _NO_DATA

    filings = data.get("filings") or []
    if not filings:
        return _NO_DATA

    lines: list[str] = [f"=== SEC Filings: {_get(data, 'symbol')} ==="]
    for i, item in enumerate(filings, 1):
        if not isinstance(item, dict):
            continue
        lines.append(f"  {i}. {_get(item, 'title')}")
        lines.append(f"     Published: {_get(item, 'publish_date')}")
        lines.append(f"     URL: {_get(item, 'url')}")
    return "\n".join(lines)


def format_earnings_calendar(data: Any) -> str:
    """Format earnings calendar response.

    API returns list: [{fiscal_year, fiscal_period, currency, expected_publish_date,
    eps_actual, eps_est, rev_actual, rev_est}]
    """
    if not data:
        return _NO_DATA
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return _NO_DATA

    lines: list[str] = ["=== Earnings Calendar ==="]
    for item in data:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"  FY{_get(item, 'fiscal_year')} Q{_get(item, 'fiscal_period')}  "
            f"Expected: {_get(item, 'expected_publish_date')}  "
            f"Currency: {_get(item, 'currency')}"
        )
        lines.append(
            f"    EPS  Actual: {_get(item, 'eps_actual'):>12s}  Est: {_get(item, 'eps_est'):>12s}"
        )
        lines.append(
            f"    Rev  Actual: {_get(item, 'rev_actual'):>12s}  Est: {_get(item, 'rev_est'):>12s}"
        )
    return "\n".join(lines)


def format_dividend_calendar(data: Any) -> str:
    """Format dividend calendar response.

    API returns list: [{symbol, market, currency, amount, div_type, declare_date,
    ex_div_date, record_date, pay_date}]
    """
    if not data:
        return _NO_DATA
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return _NO_DATA

    lines: list[str] = ["=== Dividend Calendar ==="]
    for item in data:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"  {_get(item, 'symbol')}  Amount: {_get(item, 'amount')} {_get(item, 'currency')}  "
            f"Type: {_get(item, 'div_type')}  Market: {_get(item, 'market')}"
        )
        lines.append(
            f"    Declare: {_get(item, 'declare_date')}  Ex-Div: {_get(item, 'ex_div_date')}  "
            f"Record: {_get(item, 'record_date')}  Pay: {_get(item, 'pay_date')}"
        )
    return "\n".join(lines)


def format_forecast_eps(data: Any) -> str:
    """Format forecast EPS response.

    API returns list: [{fiscal_year, fiscal_period, actual, est, reported}]
    """
    if not data:
        return _NO_DATA
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return _NO_DATA

    lines: list[str] = ["=== Forecast EPS ==="]
    for item in data:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"  FY{_get(item, 'fiscal_year')} Q{_get(item, 'fiscal_period')}  "
            f"Actual: {_get(item, 'actual'):>10s}  Est: {_get(item, 'est'):>10s}  "
            f"Reported: {_get(item, 'reported')}"
        )
    return "\n".join(lines)


def format_industry_comparison(data: Any) -> str:
    """Format industry comparison response.

    API returns: {fiscal_year, fiscal_period, industry_name, type,
    data: [{symbol, name, rank, value}]}
    """
    if not data:
        return _NO_DATA
    if not isinstance(data, dict):
        return _NO_DATA

    items = data.get("data") or []
    if not items:
        return _NO_DATA

    lines: list[str] = [
        f"=== Industry Comparison: {_get(data, 'industry_name')} ===",
        f"  Metric: {_get(data, 'type')}  "
        f"FY{_get(data, 'fiscal_year')} Q{_get(data, 'fiscal_period')}",
    ]
    for item in items:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"  #{_get(item, 'rank'):>3s}  {_get(item, 'symbol'):>10s}  "
            f"{_get(item, 'name'):<24s}  Value: {_get(item, 'value')}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Fund fundamentals formatters
# ---------------------------------------------------------------------------

def format_fund_rating(data: Any) -> str:
    """Format fund rating response.

    API returns list: [{rating_date, rating_agency, rating_cycle, rating_results}]
    """
    if not data:
        return _NO_DATA
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return _NO_DATA

    lines: list[str] = ["=== Fund Rating ==="]
    for item in data:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"  Date: {_get(item, 'rating_date')}  Agency: {_get(item, 'rating_agency')}  "
            f"Cycle: {_get(item, 'rating_cycle')}  Rating: {_get(item, 'rating_results')}"
        )
    return "\n".join(lines)


def format_fund_performance(data: Any) -> str:
    """Format fund performance response.

    API returns: {currency, end_date, return_1m, return_3m, return_6m, return_1y,
    return_3y, return_5y, return_10y, return_si}
    """
    if not data:
        return _NO_DATA
    if isinstance(data, list):
        data = data[0] if data else None
    if not data or not isinstance(data, dict):
        return _NO_DATA

    lines: list[str] = ["=== Fund Performance ==="]
    lines.append(f"  As of:    {_get(data, 'end_date')}  Currency: {_get(data, 'currency')}")
    lines.append(f"  1 Month:  {_get(data, 'return_1m')}")
    lines.append(f"  3 Months: {_get(data, 'return_3m')}")
    lines.append(f"  6 Months: {_get(data, 'return_6m')}")
    lines.append(f"  1 Year:   {_get(data, 'return_1y')}")
    lines.append(f"  3 Years:  {_get(data, 'return_3y')}")
    lines.append(f"  5 Years:  {_get(data, 'return_5y')}")
    lines.append(f"  10 Years: {_get(data, 'return_10y')}")
    lines.append(f"  Since Inception: {_get(data, 'return_si')}")
    return "\n".join(lines)


def format_fund_allocation(data: Any) -> str:
    """Format fund allocation response.

    API returns list: [{date, aum, cash, bond, stock, preferred, convertible,
    other}] where each allocation is {value, ratio}.
    """
    if not data:
        return _NO_DATA
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return _NO_DATA

    def _asset(item: dict, key: str) -> str:
        asset = item.get(key)
        if not isinstance(asset, dict):
            return "N/A"
        return f"{_get(asset, 'ratio')} ({_get(asset, 'value')})"

    lines: list[str] = ["=== Fund Allocation ==="]
    for item in data:
        if not isinstance(item, dict):
            continue
        lines.append(f"  Date: {_get(item, 'date')}  AUM: {_get(item, 'aum')}")
        lines.append(f"    Cash:        {_asset(item, 'cash')}")
        lines.append(f"    Bond:        {_asset(item, 'bond')}")
        lines.append(f"    Stock:       {_asset(item, 'stock')}")
        lines.append(f"    Preferred:   {_asset(item, 'preferred')}")
        lines.append(f"    Convertible: {_asset(item, 'convertible')}")
        lines.append(f"    Other:       {_asset(item, 'other')}")
    return "\n".join(lines)


def format_fund_holdings(data: Any) -> str:
    """Format fund holdings response.

    API returns list: [{target_symbol, stock_name, share_held_pct,
    share_held_chg_pct, maturity_date, update_time}]
    """
    if not data:
        return _NO_DATA
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return _NO_DATA

    lines: list[str] = ["=== Fund Holdings ==="]
    for item in data:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"  {_get(item, 'target_symbol'):>10s}  {_get(item, 'stock_name'):<24s}  "
            f"Held: {_get(item, 'share_held_pct')}  Chg: {_get(item, 'share_held_chg_pct')}"
        )
        if item.get("maturity_date") or item.get("update_time"):
            lines.append(
                f"{'':>12s}  Maturity: {_get(item, 'maturity_date')}  "
                f"Updated: {_get(item, 'update_time')}"
            )
    return "\n".join(lines)


def format_fund_brief(data: Any) -> str:
    """Format fund brief response.

    API returns: {name, launch_date, benchmark, investment_objective, aum, issuer,
    custodian, managers: [{name, start_date, end_date, is_incumbent, tenure_return,
    title, tenure_years, tenure_days}]}
    """
    if not data:
        return _NO_DATA
    if isinstance(data, list):
        data = data[0] if data else None
    if not data or not isinstance(data, dict):
        return _NO_DATA

    lines: list[str] = [f"=== Fund Brief: {_get(data, 'name')} ==="]
    lines.append(f"  Launch Date: {_get(data, 'launch_date')}")
    lines.append(f"  Benchmark:   {_get(data, 'benchmark')}")
    lines.append(f"  AUM:         {_get(data, 'aum')}")
    lines.append(f"  Issuer:      {_get(data, 'issuer')}")
    lines.append(f"  Custodian:   {_get(data, 'custodian')}")
    objective = data.get("investment_objective")
    if objective:
        lines.append(f"  Objective:\n    {objective}")

    managers = data.get("managers") or []
    if managers:
        lines.append("  Managers:")
        for mgr in managers:
            if not isinstance(mgr, dict):
                continue
            lines.append(
                f"    {_get(mgr, 'name')} ({_get(mgr, 'title')})  "
                f"Since: {_get(mgr, 'start_date')}  Tenure Return: {_get(mgr, 'tenure_return')}"
            )
    return "\n".join(lines)


def format_fund_dividends(data: Any) -> str:
    """Format fund dividends response.

    API returns list: [{share_date, publish_date, pay_date, record_date, dps}]
    """
    if not data:
        return _NO_DATA
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return _NO_DATA

    lines: list[str] = ["=== Fund Dividends ==="]
    for item in data:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"  DPS: {_get(item, 'dps'):>10s}  Share Date: {_get(item, 'share_date')}  "
            f"Pay: {_get(item, 'pay_date')}  Record: {_get(item, 'record_date')}  "
            f"Publish: {_get(item, 'publish_date')}"
        )
    return "\n".join(lines)


def format_fund_splits(data: Any) -> str:
    """Format fund splits response.

    API returns list: [{split_date, split_type, split_ratio, from, to}]
    """
    if not data:
        return _NO_DATA
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return _NO_DATA

    lines: list[str] = ["=== Fund Splits ==="]
    for item in data:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"  Date: {_get(item, 'split_date')}  Type: {_get(item, 'split_type')}  "
            f"Ratio: {_get(item, 'split_ratio')}  ({_get(item, 'from')} -> {_get(item, 'to')})"
        )
    return "\n".join(lines)


def format_fund_net_value(data: Any) -> str:
    """Format fund net value response.

    API returns list: [{date, currency, net_value}]
    """
    if not data:
        return _NO_DATA
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return _NO_DATA

    lines: list[str] = ["=== Fund Net Value ==="]
    for item in data:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"  {_get(item, 'date')}  NAV: {_get(item, 'net_value')} {_get(item, 'currency')}"
        )
    return "\n".join(lines)


def format_fund_files(data: Any) -> str:
    """Format fund files response.

    API returns list: [{publish_date, url, type, file_name}]
    """
    if not data:
        return _NO_DATA
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return _NO_DATA

    lines: list[str] = ["=== Fund Files ==="]
    for i, item in enumerate(data, 1):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"  {i}. {_get(item, 'file_name')}  "
            f"Type: {_get(item, 'type')}  Published: {_get(item, 'publish_date')}"
        )
        lines.append(f"     URL: {_get(item, 'url')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Financial statement formatters
# ---------------------------------------------------------------------------

def format_financial_alert(data: Any) -> str:
    """Format financial alert response.

    API returns: {start_date, end_date, fiscal_year, fiscal_period, currency,
    eps_est, eps_ly, rev_est, rev_ly}
    """
    if not data:
        return _NO_DATA
    if isinstance(data, list):
        data = data[0] if data else None
    if not data or not isinstance(data, dict):
        return _NO_DATA

    lines: list[str] = ["=== Financial Alert ==="]
    lines.append(
        f"  FY{_get(data, 'fiscal_year')} Q{_get(data, 'fiscal_period')}  "
        f"Currency: {_get(data, 'currency')}"
    )
    lines.append(f"  Window: {_get(data, 'start_date')} - {_get(data, 'end_date')}")
    lines.append(
        f"  EPS  Est: {_get(data, 'eps_est'):>12s}  Last Year: {_get(data, 'eps_ly'):>12s}"
    )
    lines.append(
        f"  Rev  Est: {_get(data, 'rev_est'):>12s}  Last Year: {_get(data, 'rev_ly'):>12s}"
    )
    return "\n".join(lines)


def format_financial_indicators(data: Any) -> str:
    """Format financial indicators response.

    API returns: {currency, values: {indicator_name: [{fiscal_year, fiscal_period,
    value}]}}
    """
    if not data:
        return _NO_DATA
    if isinstance(data, list):
        data = data[0] if data else None
    if not data or not isinstance(data, dict):
        return _NO_DATA

    values = data.get("values")
    if not isinstance(values, dict) or not values:
        return _NO_DATA

    lines: list[str] = ["=== Financial Indicators ==="]
    lines.append(f"  Currency: {_get(data, 'currency')}")
    for name, series in values.items():
        lines.append(f"  {name}:")
        if not isinstance(series, list):
            continue
        for point in series:
            if not isinstance(point, dict):
                continue
            lines.append(
                f"    FY{_get(point, 'fiscal_year')} Q{_get(point, 'fiscal_period')}: "
                f"{_get(point, 'value')}"
            )
    return "\n".join(lines)


def _format_financial_statement(data: Any, title: str, fields: list[tuple[str, str]]) -> str:
    """Shared formatter for income/balance-sheet/cash-flow statements.

    API returns list of periods, each a dict with fiscal_year, fiscal_period,
    end_date, currency, publish_date plus the statement-specific line items.
    """
    if not data:
        return _NO_DATA
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return _NO_DATA

    lines: list[str] = [f"=== {title} ==="]
    for period in data:
        if not isinstance(period, dict):
            continue
        lines.append(
            f"\n  FY{_get(period, 'fiscal_year')} Q{_get(period, 'fiscal_period')}  "
            f"End: {_get(period, 'end_date')}  Currency: {_get(period, 'currency')}  "
            f"Published: {_get(period, 'publish_date')}"
        )
        for key, label in fields:
            if period.get(key) is not None:
                lines.append(f"    {label + ':':<28s} {_get(period, key)}")
    return "\n".join(lines)


_INCOME_FIELDS: list[tuple[str, str]] = [
    ("total_revenue", "Total Revenue"),
    ("revenue", "Revenue"),
    ("cost_of_revenue", "Cost of Revenue"),
    ("gross_profit", "Gross Profit"),
    ("opex", "Operating Expense"),
    ("op_income", "Operating Income"),
    ("ebt", "Pre-Tax Income"),
    ("income_tax", "Income Tax"),
    ("net_income", "Net Income"),
    ("diluted_eps_incl_extra", "Diluted EPS"),
    ("dps", "Dividend Per Share"),
]

_BALANCE_SHEET_FIELDS: list[tuple[str, str]] = [
    ("total_assets", "Total Assets"),
    ("total_cur_assets", "Total Current Assets"),
    ("cash_st_invest", "Cash & ST Investments"),
    ("total_non_cur_assets", "Total Non-Current Assets"),
    ("total_liab", "Total Liabilities"),
    ("total_cur_liab", "Total Current Liabilities"),
    ("total_debt", "Total Debt"),
    ("total_equity", "Total Equity"),
    ("retained_earnings", "Retained Earnings"),
    ("common_shares_out", "Common Shares Outstanding"),
]

_CASHFLOW_FIELDS: list[tuple[str, str]] = [
    ("cfo", "Operating Cash Flow"),
    ("net_income", "Net Income"),
    ("dna", "Depreciation & Amortization"),
    ("cfi", "Investing Cash Flow"),
    ("capex", "Capital Expenditure"),
    ("cff", "Financing Cash Flow"),
    ("net_change_cash", "Net Change in Cash"),
    ("interest_paid", "Interest Paid"),
    ("taxes_paid", "Taxes Paid"),
]


def format_income_statement(data: Any) -> str:
    """Format income statement response."""
    return _format_financial_statement(data, "Income Statement", _INCOME_FIELDS)


def format_balance_sheet(data: Any) -> str:
    """Format balance sheet response."""
    return _format_financial_statement(data, "Balance Sheet", _BALANCE_SHEET_FIELDS)


def format_cash_flow(data: Any) -> str:
    """Format cash flow statement response."""
    return _format_financial_statement(data, "Cash Flow Statement", _CASHFLOW_FIELDS)


# ---------------------------------------------------------------------------
# Extended screener formatters (market sectors, high dividend, 52-week high/low)
# ---------------------------------------------------------------------------

def format_market_sectors(data: Any) -> str:
    """Format market sectors response.

    API returns list: [{id, name, change_ratio, volume, market_value, declined,
    advanced, flat, data: [{instrument_id, name, symbol}]}]
    """
    if not data:
        return _NO_DATA
    if isinstance(data, dict):
        data = data.get("data", data) if "data" in data else [data]
    if not isinstance(data, list) or not data:
        return _NO_DATA

    lines: list[str] = ["=== Market Sectors ==="]
    for sector in data:
        if not isinstance(sector, dict):
            continue
        lines.append(
            f"  {_get(sector, 'name')} (id: {_get(sector, 'id')})  "
            f"Change Ratio: {_get(sector, 'change_ratio')}"
        )
        lines.append(
            f"    Volume: {_get(sector, 'volume')}  Market Value: {_get(sector, 'market_value')}  "
            f"Advanced: {_get(sector, 'advanced')}  Declined: {_get(sector, 'declined')}  "
            f"Flat: {_get(sector, 'flat')}"
        )
        leaders = sector.get("data") or []
        for stock in leaders:
            if not isinstance(stock, dict):
                continue
            lines.append(
                f"      {_get(stock, 'symbol'):>10s}  {_get(stock, 'name'):<24s}  "
                f"(instrument_id: {_get(stock, 'instrument_id')})"
            )
    return "\n".join(lines)


def _format_sector_detail_stock(stock: dict) -> list[str]:
    """Format a single stock row inside a sector detail."""
    return [
        f"    {_get(stock, 'symbol'):>10s}  {_get(stock, 'name'):<24s}  "
        f"(instrument_id: {_get(stock, 'instrument_id')})",
        f"      Price: {_get(stock, 'price')}  Close: {_get(stock, 'close')}  "
        f"Change Ratio: {_get(stock, 'change_ratio')}  Amplitude: {_get(stock, 'amplitude')}",
        f"      Volume: {_get(stock, 'volume')}  Market Value: {_get(stock, 'market_value')}  "
        f"Turnover Rate: {_get(stock, 'turnover_rate')}  High: {_get(stock, 'high')}  Low: {_get(stock, 'low')}",
    ]


def format_market_sectors_detail(data: Any) -> str:
    """Format market sectors detail response.

    API returns: {id, name, change_ratio, declined, advanced, flat,
    data: [{instrument_id, category, currency, name, symbol, exchange_code, close,
    change_ratio, price, volume, market_value, turnover_rate, amplitude, high, low}]}
    """
    if not data:
        return _NO_DATA
    if isinstance(data, list):
        data = data[0] if data else None
    if not data or not isinstance(data, dict):
        return _NO_DATA

    lines: list[str] = [
        f"=== Market Sector Detail: {_get(data, 'name')} (id: {_get(data, 'id')}) ===",
        f"  Change Ratio: {_get(data, 'change_ratio')}  Advanced: {_get(data, 'advanced')}  "
        f"Declined: {_get(data, 'declined')}  Flat: {_get(data, 'flat')}",
    ]
    stocks = data.get("data") or []
    for stock in stocks:
        if isinstance(stock, dict):
            lines.extend(_format_sector_detail_stock(stock))
    return "\n".join(lines)


def format_high_dividend(data: Any) -> str:
    """Format high dividend screener response.

    API returns: {has_more, data: [{instrument_id, category, currency, name, symbol,
    ticker_symbol, exchange_code, close, change, change_ratio, price, volume,
    market_value, turnover_rate, amplitude, high, low, turnover, yield, dividend,
    ex_date, pe_ttm}]}
    """
    if not data:
        return _NO_DATA

    items = data.get("data", []) if isinstance(data, dict) else data
    if not items:
        return _NO_DATA

    lines: list[str] = ["=== High Dividend ==="]
    for item in items:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"  {_get(item, 'symbol'):>10s}  {_get(item, 'name'):<24s}  "
            f"(instrument_id: {_get(item, 'instrument_id')})"
        )
        lines.append(
            f"    Yield: {_get(item, 'yield')}  Dividend: {_get(item, 'dividend')}  "
            f"Ex-Date: {_get(item, 'ex_date')}  PE(TTM): {_get(item, 'pe_ttm')}"
        )
        lines.append(
            f"    Price: {_get(item, 'price')}  Change Ratio: {_get(item, 'change_ratio')}  "
            f"Volume: {_get(item, 'volume')}  Market Value: {_get(item, 'market_value')}"
        )

    has_more = data.get("has_more") if isinstance(data, dict) else None
    if has_more is True:
        lines.append("\n  (More results available — increase page_size or page_index)")

    return "\n".join(lines)


def format_fifty_two_week(data: Any) -> str:
    """Format 52-week high/low screener response.

    API returns: {has_more, data: [{instrument_id, category, currency, name, symbol,
    ticker_symbol, exchange_code, close, change, change_ratio, price, volume,
    market_value, turnover_rate, high, low, turnover, amplitude, price_1w, price_52w,
    change_ratio_52w, pe_ttm}]}
    """
    if not data:
        return _NO_DATA

    items = data.get("data", []) if isinstance(data, dict) else data
    if not items:
        return _NO_DATA

    lines: list[str] = ["=== 52-Week High/Low ==="]
    for item in items:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"  {_get(item, 'symbol'):>10s}  {_get(item, 'name'):<24s}  "
            f"(instrument_id: {_get(item, 'instrument_id')})"
        )
        lines.append(
            f"    Price: {_get(item, 'price')}  Change Ratio: {_get(item, 'change_ratio')}  "
            f"52W Change Ratio: {_get(item, 'change_ratio_52w')}"
        )
        lines.append(
            f"    1W Price: {_get(item, 'price_1w')}  52W Price: {_get(item, 'price_52w')}  "
            f"High: {_get(item, 'high')}  Low: {_get(item, 'low')}  PE(TTM): {_get(item, 'pe_ttm')}"
        )

    has_more = data.get("has_more") if isinstance(data, dict) else None
    if has_more is True:
        lines.append("\n  (More results available — increase page_size or page_index)")

    return "\n".join(lines)
