"""Financial statement tools for Webull MCP Server.

Provides: get_financial_alert, get_financial_indicators, get_income_statement,
get_balance_sheet, get_cash_flow. All regions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from webull_openapi_mcp.errors import handle_sdk_exception
from webull_openapi_mcp.formatters import (
    extract_response_data,
    format_balance_sheet,
    format_cash_flow,
    format_financial_alert,
    format_financial_indicators,
    format_income_statement,
    prepend_disclaimer,
)

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from webull_openapi_mcp.audit import AuditLogger
    from webull_openapi_mcp.config import ServerConfig
    from webull_openapi_mcp.sdk_client import WebullSDKClient


def register_financial_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
) -> None:
    """Register financial statement tools."""

    @mcp.tool(
        description=(
            "Get financial alert (next report estimates vs last year) for a stock. "
            "Returns: start_date, end_date, fiscal_year, fiscal_period, currency, "
            "eps_est, eps_ly, rev_est, rev_ly."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_financial_alert(
        symbol: str,
        category: str = "US_STOCK",
    ) -> str:
        """Get financial alert.

        Args:
            symbol: Security symbol (e.g. TSLA).
            category: Security type.
        """
        audit.log_tool_call("get_financial_alert", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_financials_alert(symbol=symbol, category=category)
            )
            return prepend_disclaimer(format_financial_alert(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_financial_alert", config.region_id)

    @mcp.tool(
        description=(
            "Get financial indicators (key ratios/metrics) for a stock across periods. "
            "Returns: currency and a map of indicator name to a series of "
            "{fiscal_year, fiscal_period, value}."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_financial_indicators(
        symbol: str,
        category: str = "US_STOCK",
        type: str = "QUARTERLY",
        count: int = 5,
    ) -> str:
        """Get financial indicators.

        Args:
            symbol: Security symbol (e.g. TSLA).
            category: Security type.
            type: Report type. ANNUAL or QUARTERLY (default QUARTERLY).
            count: Number of periods (default 5, max 20).
        """
        audit.log_tool_call("get_financial_indicators", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_financials_indicators(
                    symbol=symbol, category=category, type=type, count=count
                )
            )
            return prepend_disclaimer(format_financial_indicators(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_financial_indicators", config.region_id)

    @mcp.tool(
        description=(
            "Get income statement for a stock across periods. "
            "Returns per period: fiscal_year, fiscal_period, end_date, currency, "
            "total_revenue, gross_profit, op_income, net_income, diluted_eps, dps."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_income_statement(
        symbol: str,
        category: str = "US_STOCK",
        type: str = "QUARTERLY",
        count: int = 5,
    ) -> str:
        """Get income statement.

        Args:
            symbol: Security symbol (e.g. TSLA).
            category: Security type.
            type: Report type. ANNUAL or QUARTERLY (default QUARTERLY).
            count: Number of periods (default 5, max 20).
        """
        audit.log_tool_call("get_income_statement", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_financials_income(
                    symbol=symbol, category=category, type=type, count=count
                )
            )
            return prepend_disclaimer(format_income_statement(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_income_statement", config.region_id)

    @mcp.tool(
        description=(
            "Get balance sheet for a stock across periods. "
            "Returns per period: fiscal_year, fiscal_period, end_date, currency, "
            "total_assets, total_liab, total_equity, total_debt, retained_earnings, "
            "common_shares_out."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_balance_sheet(
        symbol: str,
        category: str = "US_STOCK",
        type: str = "QUARTERLY",
        count: int = 5,
    ) -> str:
        """Get balance sheet.

        Args:
            symbol: Security symbol (e.g. TSLA).
            category: Security type.
            type: Report type. ANNUAL or QUARTERLY (default QUARTERLY).
            count: Number of periods (default 5, max 20).
        """
        audit.log_tool_call("get_balance_sheet", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_financials_balance_sheet(
                    symbol=symbol, category=category, type=type, count=count
                )
            )
            return prepend_disclaimer(format_balance_sheet(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_balance_sheet", config.region_id)

    @mcp.tool(
        description=(
            "Get cash flow statement for a stock across periods. "
            "Returns per period: fiscal_year, fiscal_period, end_date, currency, "
            "cfo (operating), cfi (investing), cff (financing), capex, "
            "net_change_cash."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_cash_flow(
        symbol: str,
        category: str = "US_STOCK",
        type: str = "QUARTERLY",
        count: int = 5,
    ) -> str:
        """Get cash flow statement.

        Args:
            symbol: Security symbol (e.g. TSLA).
            category: Security type.
            type: Report type. ANNUAL or QUARTERLY (default QUARTERLY).
            count: Number of periods (default 5, max 20).
        """
        audit.log_tool_call("get_cash_flow", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_financials_cashflow(
                    symbol=symbol, category=category, type=type, count=count
                )
            )
            return prepend_disclaimer(format_cash_flow(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_cash_flow", config.region_id)
