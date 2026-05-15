"""Fundamental data tools for Webull MCP Server.

Provides: get_company_profile, get_analyst_rating, get_analyst_target_price.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from webull_openapi_mcp.errors import handle_sdk_exception
from webull_openapi_mcp.formatters import (
    extract_response_data,
    format_analyst_rating,
    format_analyst_target_price,
    format_company_profile,
    prepend_disclaimer,
)

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from webull_openapi_mcp.audit import AuditLogger
    from webull_openapi_mcp.config import ServerConfig
    from webull_openapi_mcp.sdk_client import WebullSDKClient


def register_fundamental_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
) -> None:
    """Register fundamental data tools (US only)."""

    @mcp.tool(
        description=(
            "Get company profile including business description, industry, sector, "
            "CEO, headquarters, employees, and incorporation date. "
            "Returns: symbol, category, company_name, establish_date, ceo, employees, "
            "address, profile, industries, exhibition_code."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_company_profile(
        symbol: str,
        category: str = "US_STOCK",
    ) -> str:
        """Get company profile information.

        Args:
            symbol: Security symbol (e.g. AAPL).
            category: Security type. Currently only US_STOCK.
        """
        audit.log_tool_call("get_company_profile", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.instrument.get_company_profile(symbol=symbol, category=category)
            )
            return prepend_disclaimer(format_company_profile(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_company_profile", config.region_id)

    @mcp.tool(
        description=(
            "Get analyst rating for a security. "
            "Returns: symbol, category, total number of analysts, strong_buy, buy, hold, sell, "
            "under_perform counts, and effective_start_date."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_analyst_rating(
        symbol: str,
        category: str = "US_STOCK",
    ) -> str:
        """Get analyst rating breakdown.

        Args:
            symbol: Security symbol (e.g. AAPL).
            category: Security type. Currently only US_STOCK.
        """
        audit.log_tool_call("get_analyst_rating", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.instrument.get_analyst_rating(symbol=symbol, category=category)
            )
            return prepend_disclaimer(format_analyst_rating(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_analyst_rating", config.region_id)

    @mcp.tool(
        description=(
            "Get analyst target price for a security. "
            "Returns: symbol, category, mean, low, high, median target prices, and currency."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_analyst_target_price(
        symbol: str,
        category: str = "US_STOCK",
    ) -> str:
        """Get analyst target price consensus.

        Args:
            symbol: Security symbol (e.g. AAPL).
            category: Security type. Currently only US_STOCK.
        """
        audit.log_tool_call("get_analyst_target_price", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.instrument.get_analyst_target_price(symbol=symbol, category=category)
            )
            return prepend_disclaimer(format_analyst_target_price(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_analyst_target_price", config.region_id)
