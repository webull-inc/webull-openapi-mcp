"""Tool registration & SDK-wiring tests for the 24 new fundamental/financial/screener tools."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest
from fastmcp import FastMCP

from webull_openapi_mcp.tools.market_data.fundamental import (
    register_fundamental_tools,
    register_extended_fundamental_tools,
)
from webull_openapi_mcp.tools.market_data.financial import register_financial_tools
from webull_openapi_mcp.tools.market_data.screener import (
    register_screener_tools,
    register_extended_screener_tools,
)


def _config() -> MagicMock:
    config = MagicMock()
    config.region_id = "us"
    return config


def _build_mcp() -> tuple[FastMCP, MagicMock]:
    mcp = FastMCP("test")
    sdk = MagicMock()
    audit = MagicMock()
    config = _config()
    register_fundamental_tools(mcp, sdk, audit, config)
    register_extended_fundamental_tools(mcp, sdk, audit, config)
    register_financial_tools(mcp, sdk, audit, config)
    register_screener_tools(mcp, sdk, audit, config)
    register_extended_screener_tools(mcp, sdk, audit, config)
    return mcp, sdk


def _tool_names(mcp: FastMCP) -> set[str]:
    tools = asyncio.run(mcp._list_tools())
    return {t.name for t in tools}


EXPECTED_TOOLS = [
    # stock fundamentals
    "get_stock_capital_flow",
    "get_stock_filings",
    "get_stock_earnings_calendar",
    "get_stock_dividend_calendar",
    "get_stock_forecast_eps",
    "get_stock_industry_comparison",
    # fund fundamentals
    "get_fund_rating",
    "get_fund_performance",
    "get_fund_allocation",
    "get_fund_holdings",
    "get_fund_brief",
    "get_fund_dividends",
    "get_fund_splits",
    "get_fund_net_value",
    "get_fund_files",
    # financial statements
    "get_financial_alert",
    "get_financial_indicators",
    "get_income_statement",
    "get_balance_sheet",
    "get_cash_flow",
    # screener
    "get_market_sectors",
    "get_market_sectors_detail",
    "get_high_dividend",
    "get_52_week_high_low",
]


@pytest.mark.parametrize("tool_name", EXPECTED_TOOLS)
def test_tool_registered(tool_name):
    mcp, _ = _build_mcp()
    assert tool_name in _tool_names(mcp)


def test_all_new_tools_are_read_only():
    mcp, _ = _build_mcp()
    tools = {t.name: t for t in asyncio.run(mcp._list_tools())}
    for name in EXPECTED_TOOLS:
        ann = tools[name].annotations
        read_only = getattr(ann, "readOnlyHint", None)
        assert read_only is True, f"{name} should be read-only"


def _call(mcp: FastMCP, name: str, args: dict) -> str:
    result = asyncio.run(mcp.call_tool(name, args))
    return result.content[0].text


def test_capital_flow_invokes_sdk_and_formats():
    mcp, sdk = _build_mcp()
    sdk.data.fundamentals.get_capital_flow.return_value = [
        {"date": "20260101", "large_in": "100", "large_out": "80",
         "medium_in": "50", "medium_out": "40", "small_in": "10", "small_out": "5"}
    ]
    text = _call(mcp, "get_stock_capital_flow", {"symbol": "AAPL"})
    sdk.data.fundamentals.get_capital_flow.assert_called_once_with(
        symbol="AAPL", category="US_STOCK", count=None
    )
    assert "Capital Flow" in text
    assert "20260101" in text


def test_income_statement_passes_type_and_count():
    mcp, sdk = _build_mcp()
    sdk.data.fundamentals.get_financials_income.return_value = [
        {"fiscal_year": 2025, "fiscal_period": 4, "total_revenue": "1000"}
    ]
    text = _call(mcp, "get_income_statement", {"symbol": "TSLA", "type": "ANNUAL", "count": 3})
    sdk.data.fundamentals.get_financials_income.assert_called_once_with(
        symbol="TSLA", category="US_STOCK", type="ANNUAL", count=3
    )
    assert "Income Statement" in text


def test_high_dividend_invokes_screener():
    mcp, sdk = _build_mcp()
    sdk.data.screener.get_high_dividend.return_value = {
        "has_more": False,
        "data": [{"symbol": "T", "name": "AT&T", "yield": "0.06"}],
    }
    text = _call(mcp, "get_high_dividend", {})
    sdk.data.screener.get_high_dividend.assert_called_once()
    assert "High Dividend" in text


def test_52_week_high_low_invokes_screener():
    mcp, sdk = _build_mcp()
    sdk.data.screener.get_52whl.return_value = {
        "has_more": False,
        "data": [{"symbol": "AAPL", "name": "Apple", "price": "300"}],
    }
    text = _call(mcp, "get_52_week_high_low", {"rank_type": "NEW_HIGH"})
    sdk.data.screener.get_52whl.assert_called_once()
    assert "52-Week High/Low" in text


def test_market_sectors_detail_requires_sector_id():
    mcp, sdk = _build_mcp()
    sdk.data.screener.get_market_sectors_detail.return_value = {
        "id": "1", "name": "Tech", "change_ratio": "0.01", "data": [],
    }
    text = _call(mcp, "get_market_sectors_detail", {"sector_id": "1001"})
    _, kwargs = sdk.data.screener.get_market_sectors_detail.call_args
    assert kwargs["sector_id"] == "1001"
    assert "Market Sector Detail" in text


def test_sdk_exception_is_handled_gracefully():
    mcp, sdk = _build_mcp()
    sdk.data.fundamentals.get_fund_rating.side_effect = RuntimeError("boom")
    # Should not raise; handle_sdk_exception returns a formatted error string
    text = _call(mcp, "get_fund_rating", {"symbol": "QQQ"})
    assert isinstance(text, str)
    assert text


# ---------------------------------------------------------------------------
# Region gating: new tools only in US / HK / JP
# ---------------------------------------------------------------------------

def _build_server_tools(region: str) -> set[str]:
    from unittest.mock import patch
    from webull_openapi_mcp.config import ServerConfig
    from webull_openapi_mcp import server

    cfg = MagicMock(spec=ServerConfig)
    cfg.region_id = region
    cfg.environment = "uat"
    cfg.toolsets = None
    with patch.object(server, "WebullSDKClient") as sdk_cls, patch.object(server, "AuditLogger"):
        sdk_cls.return_value = MagicMock()
        mcp = server.build_server(cfg)
    tools = asyncio.run(mcp._list_tools())
    return {t.name for t in tools}


LEGACY_TOOLS = {
    "get_company_profile",
    "get_analyst_rating",
    "get_analyst_target_price",
    "get_gainers_losers",
    "get_most_active",
}


@pytest.mark.parametrize("region", ["us", "hk", "jp"])
def test_new_tools_registered_for_supported_regions(region):
    names = _build_server_tools(region)
    missing = [t for t in EXPECTED_TOOLS if t not in names]
    assert not missing, f"{region} missing: {missing}"


@pytest.mark.parametrize("region", ["sg", "th", "my", "uk", "mx", "br"])
def test_new_tools_absent_for_unsupported_regions(region):
    names = _build_server_tools(region)
    present = [t for t in EXPECTED_TOOLS if t in names]
    assert not present, f"{region} should not expose: {present}"


@pytest.mark.parametrize("region", ["us", "hk", "jp", "sg", "th", "my", "uk", "mx", "br"])
def test_legacy_tools_available_in_all_regions(region):
    names = _build_server_tools(region)
    missing = [t for t in LEGACY_TOOLS if t not in names]
    assert not missing, f"{region} missing legacy: {missing}"
