"""Unit tests for stock & fund fundamental formatters and financial statements."""

from __future__ import annotations

import pytest

from webull_openapi_mcp.formatters import (
    format_balance_sheet,
    format_capital_flow,
    format_cash_flow,
    format_dividend_calendar,
    format_earnings_calendar,
    format_financial_alert,
    format_financial_indicators,
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
    format_income_statement,
    format_industry_comparison,
    format_sec_filings,
)


_NO_DATA = "No data available."


# ---------------------------------------------------------------------------
# Empty / None data handling
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fn", [
    format_capital_flow,
    format_sec_filings,
    format_earnings_calendar,
    format_dividend_calendar,
    format_forecast_eps,
    format_industry_comparison,
    format_fund_rating,
    format_fund_performance,
    format_fund_allocation,
    format_fund_holdings,
    format_fund_brief,
    format_fund_dividends,
    format_fund_splits,
    format_fund_net_value,
    format_fund_files,
    format_financial_alert,
    format_financial_indicators,
    format_income_statement,
    format_balance_sheet,
    format_cash_flow,
])
def test_returns_no_data_for_none(fn):
    assert fn(None) == _NO_DATA


@pytest.mark.parametrize("fn", [
    format_capital_flow,
    format_earnings_calendar,
    format_dividend_calendar,
    format_forecast_eps,
    format_fund_rating,
    format_fund_holdings,
    format_fund_dividends,
    format_fund_splits,
    format_fund_net_value,
    format_fund_files,
    format_income_statement,
    format_balance_sheet,
    format_cash_flow,
])
def test_returns_no_data_for_empty_list(fn):
    assert fn([]) == _NO_DATA


# ---------------------------------------------------------------------------
# Stock fundamentals
# ---------------------------------------------------------------------------

class TestFormatCapitalFlow:
    def test_formats_data(self):
        data = [
            {
                "date": "20260101",
                "large_in": "1000",
                "large_out": "800",
                "medium_in": "500",
                "medium_out": "400",
                "small_in": "100",
                "small_out": "50",
            },
        ]
        result = format_capital_flow(data)
        assert "Capital Flow" in result
        assert "20260101" in result
        assert "1000" in result
        assert "800" in result
        assert "500" in result
        assert "50" in result

    def test_single_dict_wrapped(self):
        data = {"date": "20260102", "large_in": "10"}
        result = format_capital_flow(data)
        assert "20260102" in result


class TestFormatSecFilings:
    def test_formats_filings(self):
        data = {
            "symbol": "AAPL",
            "category": "US_STOCK",
            "filings": [
                {
                    "title": "10-K Annual Report",
                    "url": "https://sec.gov/aapl-10k",
                    "publish_date": "2026-01-15",
                },
            ],
        }
        result = format_sec_filings(data)
        assert "AAPL" in result
        assert "10-K Annual Report" in result
        assert "https://sec.gov/aapl-10k" in result
        assert "2026-01-15" in result

    def test_empty_filings_list(self):
        assert format_sec_filings({"symbol": "AAPL", "filings": []}) == _NO_DATA

    def test_non_dict_returns_no_data(self):
        assert format_sec_filings([{"title": "x"}]) == _NO_DATA


class TestFormatEarningsCalendar:
    def test_formats_data(self):
        data = [
            {
                "fiscal_year": 2026,
                "fiscal_period": 1,
                "currency": "USD",
                "expected_publish_date": "2026-04-30",
                "eps_actual": "1.5",
                "eps_est": "1.4",
                "rev_actual": "100000",
                "rev_est": "98000",
            },
        ]
        result = format_earnings_calendar(data)
        assert "Earnings Calendar" in result
        assert "FY2026 Q1" in result
        assert "2026-04-30" in result
        assert "1.5" in result
        assert "98000" in result


class TestFormatDividendCalendar:
    def test_formats_data(self):
        data = [
            {
                "symbol": "AAPL",
                "market": "US",
                "currency": "USD",
                "amount": "0.24",
                "div_type": "CASH",
                "declare_date": "2026-01-01",
                "ex_div_date": "2026-02-01",
                "record_date": "2026-02-02",
                "pay_date": "2026-02-15",
            },
        ]
        result = format_dividend_calendar(data)
        assert "Dividend Calendar" in result
        assert "AAPL" in result
        assert "0.24" in result
        assert "CASH" in result
        assert "2026-02-15" in result


class TestFormatForecastEps:
    def test_formats_data(self):
        data = [
            {"fiscal_year": 2025, "fiscal_period": 4, "actual": "2.1", "est": "2.0", "reported": True},
            {"fiscal_year": 2026, "fiscal_period": 1, "actual": None, "est": "2.3", "reported": False},
        ]
        result = format_forecast_eps(data)
        assert "Forecast EPS" in result
        assert "FY2025 Q4" in result
        assert "2.1" in result
        assert "FY2026 Q1" in result
        assert "2.3" in result


class TestFormatIndustryComparison:
    def test_formats_data(self):
        data = {
            "industry_name": "Semiconductors",
            "type": "PE_TTM",
            "fiscal_year": 2026,
            "fiscal_period": 1,
            "data": [
                {"symbol": "NVDA", "name": "NVIDIA", "rank": 1, "value": "60"},
                {"symbol": "AMD", "name": "AMD", "rank": 2, "value": "45"},
            ],
        }
        result = format_industry_comparison(data)
        assert "Semiconductors" in result
        assert "PE_TTM" in result
        assert "NVDA" in result
        assert "AMD" in result
        assert "60" in result

    def test_empty_data_list(self):
        assert format_industry_comparison({"industry_name": "X", "data": []}) == _NO_DATA

    def test_non_dict_returns_no_data(self):
        assert format_industry_comparison([{"symbol": "X"}]) == _NO_DATA


# ---------------------------------------------------------------------------
# Fund fundamentals
# ---------------------------------------------------------------------------

class TestFormatFundRating:
    def test_formats_data(self):
        data = [
            {
                "rating_date": "2026-01-01",
                "rating_agency": "Morningstar",
                "rating_cycle": "3Y",
                "rating_results": 5,
            },
        ]
        result = format_fund_rating(data)
        assert "Fund Rating" in result
        assert "Morningstar" in result
        assert "3Y" in result
        assert "5" in result


class TestFormatFundPerformance:
    def test_formats_data(self):
        data = {
            "currency": "USD",
            "end_date": "2026-01-31",
            "return_1m": "0.02",
            "return_3m": "0.05",
            "return_6m": "0.08",
            "return_1y": "0.15",
            "return_3y": "0.40",
            "return_5y": "0.90",
            "return_10y": "2.5",
            "return_si": "3.1",
        }
        result = format_fund_performance(data)
        assert "Fund Performance" in result
        assert "2026-01-31" in result
        assert "0.15" in result
        assert "Since Inception" in result
        assert "3.1" in result

    def test_handles_list_input(self):
        data = [{"end_date": "2026-01-31", "return_1y": "0.1"}]
        result = format_fund_performance(data)
        assert "0.1" in result


class TestFormatFundAllocation:
    def test_formats_data(self):
        data = [
            {
                "date": "2026-01-31",
                "aum": "1000000000",
                "cash": {"value": "100", "ratio": "0.1"},
                "bond": {"value": "200", "ratio": "0.2"},
                "stock": {"value": "700", "ratio": "0.7"},
            },
        ]
        result = format_fund_allocation(data)
        assert "Fund Allocation" in result
        assert "2026-01-31" in result
        assert "0.7" in result
        assert "Stock" in result

    def test_handles_missing_asset(self):
        data = [{"date": "2026-01-31", "aum": "1"}]
        result = format_fund_allocation(data)
        assert "N/A" in result


class TestFormatFundHoldings:
    def test_formats_data(self):
        data = [
            {
                "target_symbol": "AAPL",
                "stock_name": "Apple Inc",
                "share_held_pct": "0.08",
                "share_held_chg_pct": "0.01",
                "maturity_date": "N/A",
                "update_time": "2026-01-31",
            },
        ]
        result = format_fund_holdings(data)
        assert "Fund Holdings" in result
        assert "AAPL" in result
        assert "Apple Inc" in result
        assert "0.08" in result


class TestFormatFundBrief:
    def test_formats_data(self):
        data = {
            "name": "Invesco QQQ Trust",
            "launch_date": "1999-03-10",
            "benchmark": "Nasdaq-100",
            "investment_objective": "Track the Nasdaq-100 Index.",
            "aum": "300000000000",
            "issuer": "Invesco",
            "custodian": "BNY Mellon",
            "managers": [
                {"name": "John Doe", "title": "Lead PM", "start_date": "2010-01-01", "tenure_return": "0.5"},
            ],
        }
        result = format_fund_brief(data)
        assert "Invesco QQQ Trust" in result
        assert "Nasdaq-100" in result
        assert "Invesco" in result
        assert "John Doe" in result
        assert "Track the Nasdaq-100 Index." in result

    def test_no_managers(self):
        data = {"name": "Fund X"}
        result = format_fund_brief(data)
        assert "Fund X" in result
        assert "Managers" not in result


class TestFormatFundDividends:
    def test_formats_data(self):
        data = [
            {
                "share_date": "2026-01-01",
                "publish_date": "2026-01-02",
                "pay_date": "2026-01-15",
                "record_date": "2026-01-03",
                "dps": "0.5",
            },
        ]
        result = format_fund_dividends(data)
        assert "Fund Dividends" in result
        assert "0.5" in result
        assert "2026-01-15" in result


class TestFormatFundSplits:
    def test_formats_data(self):
        data = [
            {
                "split_date": "2026-01-01",
                "split_type": "FORWARD",
                "split_ratio": "2:1",
                "from": 1,
                "to": 2,
            },
        ]
        result = format_fund_splits(data)
        assert "Fund Splits" in result
        assert "FORWARD" in result
        assert "2:1" in result


class TestFormatFundNetValue:
    def test_formats_data(self):
        data = [
            {"date": "2026-01-31", "currency": "USD", "net_value": "450.25"},
        ]
        result = format_fund_net_value(data)
        assert "Fund Net Value" in result
        assert "2026-01-31" in result
        assert "450.25" in result
        assert "USD" in result


class TestFormatFundFiles:
    def test_formats_data(self):
        data = [
            {
                "publish_date": "2026-01-01",
                "url": "https://fund.com/prospectus.pdf",
                "type": 1,
                "file_name": "Prospectus",
            },
        ]
        result = format_fund_files(data)
        assert "Fund Files" in result
        assert "Prospectus" in result
        assert "https://fund.com/prospectus.pdf" in result


# ---------------------------------------------------------------------------
# Financial statements
# ---------------------------------------------------------------------------

class TestFormatFinancialAlert:
    def test_formats_data(self):
        data = {
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "fiscal_year": 2026,
            "fiscal_period": 1,
            "currency": "USD",
            "eps_est": "1.5",
            "eps_ly": "1.2",
            "rev_est": "100000",
            "rev_ly": "90000",
        }
        result = format_financial_alert(data)
        assert "Financial Alert" in result
        assert "FY2026 Q1" in result
        assert "1.5" in result
        assert "90000" in result

    def test_handles_list_input(self):
        data = [{"fiscal_year": 2026, "fiscal_period": 1, "eps_est": "1.5"}]
        result = format_financial_alert(data)
        assert "1.5" in result


class TestFormatFinancialIndicators:
    def test_formats_data(self):
        data = {
            "currency": "USD",
            "values": {
                "ROE": [
                    {"fiscal_year": 2025, "fiscal_period": 4, "value": "0.3"},
                    {"fiscal_year": 2026, "fiscal_period": 1, "value": "0.32"},
                ],
                "PE_TTM": [
                    {"fiscal_year": 2026, "fiscal_period": 1, "value": "30"},
                ],
            },
        }
        result = format_financial_indicators(data)
        assert "Financial Indicators" in result
        assert "ROE" in result
        assert "PE_TTM" in result
        assert "0.32" in result
        assert "FY2026 Q1" in result

    def test_empty_values_returns_no_data(self):
        assert format_financial_indicators({"currency": "USD", "values": {}}) == _NO_DATA


class TestFormatIncomeStatement:
    def test_formats_data(self):
        data = [
            {
                "fiscal_year": 2025,
                "fiscal_period": 4,
                "end_date": "2025-12-31",
                "currency": "USD",
                "total_revenue": "1000",
                "gross_profit": "600",
                "op_income": "400",
                "net_income": "300",
                "diluted_eps_incl_extra": "2.5",
                "dps": "0.5",
            },
        ]
        result = format_income_statement(data)
        assert "Income Statement" in result
        assert "FY2025 Q4" in result
        assert "Total Revenue" in result
        assert "1000" in result
        assert "Diluted EPS" in result
        assert "2.5" in result

    def test_skips_missing_fields(self):
        data = [{"fiscal_year": 2025, "fiscal_period": 4, "total_revenue": "1000"}]
        result = format_income_statement(data)
        assert "Total Revenue" in result
        assert "Net Income" not in result


class TestFormatBalanceSheet:
    def test_formats_data(self):
        data = [
            {
                "fiscal_year": 2025,
                "fiscal_period": 4,
                "end_date": "2025-12-31",
                "currency": "USD",
                "total_assets": "5000",
                "total_liab": "2000",
                "total_equity": "3000",
                "total_debt": "1000",
                "retained_earnings": "1500",
                "common_shares_out": "100",
            },
        ]
        result = format_balance_sheet(data)
        assert "Balance Sheet" in result
        assert "Total Assets" in result
        assert "5000" in result
        assert "Total Equity" in result
        assert "3000" in result


class TestFormatCashFlow:
    def test_formats_data(self):
        data = [
            {
                "fiscal_year": 2025,
                "fiscal_period": 4,
                "end_date": "2025-12-31",
                "currency": "USD",
                "cfo": "800",
                "cfi": "-300",
                "cff": "-200",
                "capex": "-250",
                "net_change_cash": "300",
            },
        ]
        result = format_cash_flow(data)
        assert "Cash Flow Statement" in result
        assert "Operating Cash Flow" in result
        assert "800" in result
        assert "Capital Expenditure" in result
        assert "-250" in result
