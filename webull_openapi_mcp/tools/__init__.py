"""Tool registration functions for Webull MCP Server.

Each register_*_tools function takes a FastMCP instance and registers
tools using @mcp.tool() decorators.
"""

from webull_openapi_mcp.tools.trading.account import register_account_tools
from webull_openapi_mcp.tools.trading.assets import register_assets_tools
from webull_openapi_mcp.tools.trading.order import register_order_tools
from webull_openapi_mcp.tools.trading.instrument import register_instrument_tools
from webull_openapi_mcp.tools.trading.stock_order import register_stock_order_tools
from webull_openapi_mcp.tools.trading.stock_order import register_combo_order_tools
from webull_openapi_mcp.tools.trading.stock_order import register_algo_order_tools
from webull_openapi_mcp.tools.trading.option_order import register_option_single_tools
from webull_openapi_mcp.tools.trading.option_order import register_option_strategy_tools
from webull_openapi_mcp.tools.trading.futures_order import register_futures_order_tools
from webull_openapi_mcp.tools.trading.crypto_order import register_crypto_order_tools
from webull_openapi_mcp.tools.trading.event_order import register_event_order_tools
from webull_openapi_mcp.tools.market_data.stock import register_stock_market_data_tools
from webull_openapi_mcp.tools.market_data.futures import register_futures_market_data_tools
from webull_openapi_mcp.tools.market_data.crypto import register_crypto_market_data_tools
from webull_openapi_mcp.tools.market_data.event import register_event_market_data_tools
from webull_openapi_mcp.tools.market_data.option import register_option_market_data_tools
from webull_openapi_mcp.tools.market_data.screener import register_screener_tools
from webull_openapi_mcp.tools.market_data.screener import register_extended_screener_tools
from webull_openapi_mcp.tools.market_data.watchlist import register_watchlist_tools
from webull_openapi_mcp.tools.market_data.fundamental import register_fundamental_tools
from webull_openapi_mcp.tools.market_data.fundamental import register_extended_fundamental_tools
from webull_openapi_mcp.tools.market_data.financial import register_financial_tools

__all__ = [
    "register_account_tools",
    "register_assets_tools",
    "register_order_tools",
    "register_instrument_tools",
    "register_stock_order_tools",
    "register_combo_order_tools",
    "register_algo_order_tools",
    "register_option_single_tools",
    "register_option_strategy_tools",
    "register_futures_order_tools",
    "register_crypto_order_tools",
    "register_event_order_tools",
    "register_stock_market_data_tools",
    "register_futures_market_data_tools",
    "register_crypto_market_data_tools",
    "register_event_market_data_tools",
    "register_option_market_data_tools",
    "register_screener_tools",
    "register_extended_screener_tools",
    "register_watchlist_tools",
    "register_fundamental_tools",
    "register_extended_fundamental_tools",
    "register_financial_tools",
]
