"""Fundamental data tools for Webull MCP Server.

Provides:
- register_fundamental_tools: company profile & analyst data (all regions).
- register_extended_fundamental_tools: stock fundamentals (capital flow, SEC
  filings, earnings/dividend calendar, forecast EPS, industry comparison) and
  fund fundamentals (rating, performance, allocation, holdings, brief, dividends,
  splits, net value, files). US / HK / JP only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from webull_openapi_mcp.errors import handle_sdk_exception
from webull_openapi_mcp.formatters import (
    extract_response_data,
    format_analyst_rating,
    format_analyst_target_price,
    format_capital_flow,
    format_company_profile,
    format_dividend_calendar,
    format_earnings_calendar,
    format_forecast_eps,
    format_fund_allocation,
    format_fund_brief,
    format_fund_dividends,
    format_fund_files,
    format_fund_holdings,
    format_fund_net_value,
    format_fund_performance,
    format_fund_rating,
    format_fund_splits,
    format_industry_comparison,
    format_sec_filings,
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
    """Register company profile & analyst data tools (all regions)."""

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


def register_extended_fundamental_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
) -> None:
    """Register stock & fund fundamental tools (US / HK / JP only).

    Covers capital flow, SEC filings, earnings/dividend calendars, forecast EPS,
    industry comparison, and the full fund data suite.
    """

    # ------------------------------------------------------------------
    # Stock fundamentals
    # ------------------------------------------------------------------

    @mcp.tool(
        description=(
            "Get capital flow distribution for a stock by date. "
            "Returns: date, large_in, large_out, medium_in, medium_out, "
            "small_in, small_out."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_stock_capital_flow(
        symbol: str,
        category: str = "US_STOCK",
        count: Optional[int] = None,
    ) -> str:
        """Get stock capital flow distribution.

        Args:
            symbol: Security symbol (e.g. AAPL).
            category: Security type. Supports US_STOCK, HK_STOCK, CN_STOCK, JP_STOCK.
            count: Number of records (default 5, range 1-5).
        """
        audit.log_tool_call("get_stock_capital_flow", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_capital_flow(
                    symbol=symbol, category=category, count=count
                )
            )
            return prepend_disclaimer(format_capital_flow(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_stock_capital_flow", config.region_id)

    @mcp.tool(
        description=(
            "Get SEC filings for a US stock (last 3 years). "
            "Returns: symbol, category, and a list of filings with title, "
            "url, publish_date."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_stock_filings(
        symbol: str,
        category: str = "US_STOCK",
    ) -> str:
        """Get SEC filings for a stock.

        Args:
            symbol: Security symbol (e.g. AAPL).
            category: Security type. Only US_STOCK supported.
        """
        audit.log_tool_call("get_stock_filings", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_sec_filings(symbol=symbol, category=category)
            )
            return prepend_disclaimer(format_sec_filings(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_stock_filings", config.region_id)

    @mcp.tool(
        description=(
            "Get earnings calendar for a stock (half a year before/after today, "
            "sorted ascending). Reports with an eps_actual value are already published. "
            "Returns: fiscal_year, fiscal_period, currency, expected_publish_date, "
            "eps_actual, eps_est, rev_actual, rev_est."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_stock_earnings_calendar(
        symbol: str,
        category: str = "US_STOCK",
    ) -> str:
        """Get earnings calendar for a stock.

        Args:
            symbol: Security symbol (e.g. AAPL).
            category: Security type. Supports US_STOCK, HK_STOCK, CN_STOCK, JP_STOCK.
        """
        audit.log_tool_call("get_stock_earnings_calendar", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_earnings_calendar(symbol=symbol, category=category)
            )
            return prepend_disclaimer(format_earnings_calendar(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_stock_earnings_calendar", config.region_id)

    @mcp.tool(
        description=(
            "Get dividend calendar for a stock (half a year before/after today, "
            "sorted ascending). "
            "Returns: symbol, market, currency, amount, div_type, declare_date, "
            "ex_div_date, record_date, pay_date."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_stock_dividend_calendar(
        symbol: str,
        category: str = "US_STOCK",
    ) -> str:
        """Get dividend calendar for a stock.

        Args:
            symbol: Security symbol (e.g. AAPL).
            category: Security type. Supports US_STOCK, HK_STOCK, CN_STOCK, JP_STOCK.
        """
        audit.log_tool_call("get_stock_dividend_calendar", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_dividend_calendar(symbol=symbol, category=category)
            )
            return prepend_disclaimer(format_dividend_calendar(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_stock_dividend_calendar", config.region_id)

    @mcp.tool(
        description=(
            "Get forecast EPS for a stock: actual EPS of the most recent four "
            "disclosed fiscal periods plus latest analyst consensus estimate "
            "(up to 5 records, ascending). "
            "Returns: fiscal_year, fiscal_period, actual, est, reported."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_stock_forecast_eps(
        symbol: str,
        category: str = "US_STOCK",
    ) -> str:
        """Get forecast EPS for a stock.

        Args:
            symbol: Security symbol (e.g. AAPL). Single symbol only.
            category: Security type. Supports US_STOCK, HK_STOCK, CN_STOCK.
        """
        audit.log_tool_call("get_stock_forecast_eps", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_forecast_eps(symbol=symbol, category=category)
            )
            return prepend_disclaimer(format_forecast_eps(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_stock_forecast_eps", config.region_id)

    @mcp.tool(
        description=(
            "Get industry comparison for a stock (up to 20 peers in the same industry). "
            "Returns: industry_name, type, fiscal_year, fiscal_period, and a ranked "
            "list of {symbol, name, rank, value}."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_stock_industry_comparison(
        symbol: str,
        category: str = "US_STOCK",
        sort_by: Optional[str] = None,
    ) -> str:
        """Get industry comparison for a stock.

        Args:
            symbol: Security symbol (e.g. AAPL).
            category: Security type. Supports US_STOCK, HK_STOCK, CN_STOCK.
            sort_by: Sort metric. Default EPS_TTM. Options: EPS_TTM, NAPS, DPS_TTM,
                ROE, DEBT_TO_ASSETS, NET_MARGIN, DIV_YIELD_TTM, PE_TTM, PB_RATIO.
        """
        audit.log_tool_call("get_stock_industry_comparison", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_industry_comparison(
                    symbol=symbol, category=category, sort_by=sort_by
                )
            )
            return prepend_disclaimer(format_industry_comparison(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_stock_industry_comparison", config.region_id)

    # ------------------------------------------------------------------
    # Fund fundamentals
    # ------------------------------------------------------------------

    @mcp.tool(
        description=(
            "Get fund rating history. "
            "Returns: rating_date, rating_agency, rating_cycle, rating_results."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_fund_rating(
        symbol: str,
        category: str = "US_STOCK",
    ) -> str:
        """Get fund rating.

        Args:
            symbol: Fund symbol (e.g. QQQ).
            category: Security type.
        """
        audit.log_tool_call("get_fund_rating", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_fund_rating(symbol=symbol, category=category)
            )
            return prepend_disclaimer(format_fund_rating(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_fund_rating", config.region_id)

    @mcp.tool(
        description=(
            "Get fund performance returns over multiple horizons. "
            "Returns: currency, end_date, return_1m, return_3m, return_6m, return_1y, "
            "return_3y, return_5y, return_10y, return_si."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_fund_performance(
        symbol: str,
        category: str = "US_STOCK",
    ) -> str:
        """Get fund performance.

        Args:
            symbol: Fund symbol (e.g. QQQ).
            category: Security type.
        """
        audit.log_tool_call("get_fund_performance", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_fund_performance(symbol=symbol, category=category)
            )
            return prepend_disclaimer(format_fund_performance(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_fund_performance", config.region_id)

    @mcp.tool(
        description=(
            "Get fund asset allocation by date. "
            "Returns: date, aum, and cash/bond/stock/preferred/convertible/other "
            "allocations each with value and ratio."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_fund_allocation(
        symbol: str,
        category: str = "US_STOCK",
    ) -> str:
        """Get fund asset allocation.

        Args:
            symbol: Fund symbol (e.g. QQQ).
            category: Security type.
        """
        audit.log_tool_call("get_fund_allocation", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_fund_allocation(symbol=symbol, category=category)
            )
            return prepend_disclaimer(format_fund_allocation(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_fund_allocation", config.region_id)

    @mcp.tool(
        description=(
            "Get fund top 10 holdings. "
            "Returns: target_symbol, stock_name, share_held_pct, share_held_chg_pct, "
            "maturity_date, update_time."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_fund_holdings(
        symbol: str,
        category: str = "US_STOCK",
    ) -> str:
        """Get fund top 10 holdings.

        Args:
            symbol: Fund symbol (e.g. QQQ).
            category: Security type.
        """
        audit.log_tool_call("get_fund_holdings", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_fund_holdings(symbol=symbol, category=category)
            )
            return prepend_disclaimer(format_fund_holdings(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_fund_holdings", config.region_id)

    @mcp.tool(
        description=(
            "Get fund brief information. "
            "Returns: name, launch_date, benchmark, investment_objective, aum, "
            "issuer, custodian, and managers list."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_fund_brief(
        symbol: str,
        category: str = "US_STOCK",
    ) -> str:
        """Get fund brief.

        Args:
            symbol: Fund symbol (e.g. QQQ).
            category: Security type.
        """
        audit.log_tool_call("get_fund_brief", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_fund_brief(symbol=symbol, category=category)
            )
            return prepend_disclaimer(format_fund_brief(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_fund_brief", config.region_id)

    @mcp.tool(
        description=(
            "Get fund dividend history (paginated). "
            "Returns: share_date, publish_date, pay_date, record_date, dps."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_fund_dividends(
        symbol: str,
        category: str = "US_STOCK",
        page_index: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> str:
        """Get fund dividends.

        Args:
            symbol: Fund symbol (e.g. QQQ).
            category: Security type.
            page_index: Page number starting from 1 (default 1).
            page_size: Records per page (default 10, max 20).
        """
        audit.log_tool_call("get_fund_dividends", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_fund_dividends(
                    symbol=symbol, category=category,
                    page_index=page_index, page_size=page_size,
                )
            )
            return prepend_disclaimer(format_fund_dividends(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_fund_dividends", config.region_id)

    @mcp.tool(
        description=(
            "Get fund split history. "
            "Returns: split_date, split_type, split_ratio, from, to."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_fund_splits(
        symbol: str,
        category: str = "US_STOCK",
    ) -> str:
        """Get fund splits.

        Args:
            symbol: Fund symbol (e.g. QQQ).
            category: Security type.
        """
        audit.log_tool_call("get_fund_splits", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_fund_splits(symbol=symbol, category=category)
            )
            return prepend_disclaimer(format_fund_splits(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_fund_splits", config.region_id)

    @mcp.tool(
        description=(
            "Get fund net value (NAV) history. "
            "Returns: date, currency, net_value."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_fund_net_value(
        symbol: str,
        category: str = "US_STOCK",
        last_date: Optional[str] = None,
        count: Optional[int] = None,
    ) -> str:
        """Get fund net value.

        Args:
            symbol: Fund symbol (e.g. QQQ).
            category: Security type.
            last_date: Last query date for pagination (e.g. 2026-04-01).
            count: Records per query (default 5, max 20).
        """
        audit.log_tool_call("get_fund_net_value", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_fund_net_value(
                    symbol=symbol, category=category,
                    last_date=last_date, count=count,
                )
            )
            return prepend_disclaimer(format_fund_net_value(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_fund_net_value", config.region_id)

    @mcp.tool(
        description=(
            "Get fund files/documents. "
            "Returns: publish_date, url, type, file_name."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_fund_files(
        symbol: str,
        category: str = "US_STOCK",
    ) -> str:
        """Get fund files.

        Args:
            symbol: Fund symbol (e.g. QQQ).
            category: Security type.
        """
        audit.log_tool_call("get_fund_files", {"symbol": symbol})
        try:
            data = extract_response_data(
                sdk.data.fundamentals.get_fund_files(symbol=symbol, category=category)
            )
            return prepend_disclaimer(format_fund_files(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_fund_files", config.region_id)
