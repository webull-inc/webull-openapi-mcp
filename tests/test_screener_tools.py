"""Unit tests for extended screener formatters (market sectors, high dividend, 52-week high/low)."""

from __future__ import annotations

import pytest

from webull_openapi_mcp.formatters import (
    format_fifty_two_week,
    format_high_dividend,
    format_market_sectors,
    format_market_sectors_detail,
)


_NO_DATA = "No data available."


# ---------------------------------------------------------------------------
# Empty / None data handling
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fn", [
    format_market_sectors,
    format_market_sectors_detail,
    format_high_dividend,
    format_fifty_two_week,
])
def test_returns_no_data_for_none(fn):
    assert fn(None) == _NO_DATA


@pytest.mark.parametrize("fn", [
    format_market_sectors,
    format_high_dividend,
    format_fifty_two_week,
])
def test_returns_no_data_for_empty_list(fn):
    assert fn([]) == _NO_DATA


# ---------------------------------------------------------------------------
# Market Sectors
# ---------------------------------------------------------------------------

class TestFormatMarketSectors:
    def test_formats_data_list(self):
        data = [
            {
                "id": "1001",
                "name": "Technology",
                "change_ratio": "0.015",
                "volume": "5000000",
                "market_value": "10000000000000",
                "advanced": "120",
                "declined": "30",
                "flat": "5",
                "data": [
                    {"instrument_id": "913256135", "name": "Apple Inc", "symbol": "AAPL"},
                ],
            },
        ]
        result = format_market_sectors(data)
        assert "Market Sectors" in result
        assert "Technology" in result
        assert "1001" in result
        assert "0.015" in result
        assert "AAPL" in result
        assert "Apple Inc" in result

    def test_wrapped_in_data_key(self):
        data = {"data": [{"id": "1", "name": "Energy", "change_ratio": "0.02"}]}
        result = format_market_sectors(data)
        assert "Energy" in result

    def test_empty_data_key(self):
        assert format_market_sectors({"data": []}) == _NO_DATA


# ---------------------------------------------------------------------------
# Market Sectors Detail
# ---------------------------------------------------------------------------

class TestFormatMarketSectorsDetail:
    def test_formats_data(self):
        data = {
            "id": "1001",
            "name": "Technology",
            "change_ratio": "0.015",
            "advanced": "120",
            "declined": "30",
            "flat": "5",
            "data": [
                {
                    "instrument_id": "913256135",
                    "symbol": "AAPL",
                    "name": "Apple Inc",
                    "price": "290.00",
                    "close": "285.00",
                    "change_ratio": "0.018",
                    "amplitude": "0.025",
                    "volume": "80000000",
                    "market_value": "4500000000000",
                    "turnover_rate": "0.005",
                    "high": "291.00",
                    "low": "284.00",
                },
            ],
        }
        result = format_market_sectors_detail(data)
        assert "Market Sector Detail: Technology" in result
        assert "1001" in result
        assert "AAPL" in result
        assert "Apple Inc" in result
        assert "290.00" in result
        assert "0.018" in result

    def test_handles_list_input(self):
        data = [{"id": "1", "name": "Energy", "change_ratio": "0.02", "data": []}]
        result = format_market_sectors_detail(data)
        assert "Energy" in result

    def test_none_returns_no_data(self):
        assert format_market_sectors_detail(None) == _NO_DATA


# ---------------------------------------------------------------------------
# High Dividend
# ---------------------------------------------------------------------------

class TestFormatHighDividend:
    def test_formats_data(self):
        data = {
            "has_more": True,
            "data": [
                {
                    "instrument_id": "913256",
                    "symbol": "T",
                    "name": "AT&T Inc",
                    "price": "20.00",
                    "change_ratio": "0.01",
                    "volume": "30000000",
                    "market_value": "150000000000",
                    "yield": "0.06",
                    "dividend": "1.11",
                    "ex_date": "2026-01-09",
                    "pe_ttm": "8.5",
                },
            ],
        }
        result = format_high_dividend(data)
        assert "High Dividend" in result
        assert "AT&T Inc" in result
        assert "0.06" in result
        assert "1.11" in result
        assert "2026-01-09" in result
        assert "More results available" in result

    def test_no_has_more(self):
        data = {"has_more": False, "data": [{"symbol": "T", "name": "AT&T", "yield": "0.06"}]}
        result = format_high_dividend(data)
        assert "More results available" not in result

    def test_empty_data_list(self):
        assert format_high_dividend({"has_more": False, "data": []}) == _NO_DATA


# ---------------------------------------------------------------------------
# 52-Week High/Low
# ---------------------------------------------------------------------------

class TestFormatFiftyTwoWeek:
    def test_formats_data(self):
        data = {
            "has_more": False,
            "data": [
                {
                    "instrument_id": "913256135",
                    "symbol": "AAPL",
                    "name": "Apple Inc",
                    "price": "300.00",
                    "change_ratio": "0.02",
                    "change_ratio_52w": "0.55",
                    "price_1w": "290.00",
                    "price_52w": "200.00",
                    "high": "305.00",
                    "low": "295.00",
                    "pe_ttm": "30.0",
                },
            ],
        }
        result = format_fifty_two_week(data)
        assert "52-Week High/Low" in result
        assert "AAPL" in result
        assert "Apple Inc" in result
        assert "0.55" in result
        assert "200.00" in result
        assert "30.0" in result

    def test_has_more_flag(self):
        data = {"has_more": True, "data": [{"symbol": "AAPL", "name": "Apple", "price": "300"}]}
        result = format_fifty_two_week(data)
        assert "More results available" in result

    def test_empty_data_list(self):
        assert format_fifty_two_week({"has_more": False, "data": []}) == _NO_DATA
