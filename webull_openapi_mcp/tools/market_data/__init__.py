"""Market Data API tools for Webull MCP Server.

Provides register_*_tools functions for accessing market data across asset types:
- Stock: US stocks and ETFs market data
- Futures: Futures market data
- Crypto: Cryptocurrency market data
- Event: Event contract market data
"""

from webull_openapi_mcp.tools.market_data.stock import register_stock_market_data_tools
from webull_openapi_mcp.tools.market_data.futures import register_futures_market_data_tools
from webull_openapi_mcp.tools.market_data.crypto import register_crypto_market_data_tools
from webull_openapi_mcp.tools.market_data.event import register_event_market_data_tools
from webull_openapi_mcp.tools.market_data.option import register_option_market_data_tools

__all__ = [
    "register_stock_market_data_tools",
    "register_futures_market_data_tools",
    "register_crypto_market_data_tools",
    "register_event_market_data_tools",
    "register_option_market_data_tools",
]
