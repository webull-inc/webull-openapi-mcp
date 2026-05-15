"""Unit tests for market data tools (screener, watchlist, NOII, stock bars start_time/end_time)."""

from __future__ import annotations

import pytest

from webull_openapi_mcp.formatters import (
    format_gainers_losers,
    format_most_active,
    format_noii_bars,
    format_noii_snapshot,
    format_watchlist,
    format_watchlist_instruments,
)


_NO_DATA = "No data available."


# ---------------------------------------------------------------------------
# Empty / None data handling
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fn", [
    format_gainers_losers,
    format_most_active,
    format_noii_bars,
    format_noii_snapshot,
    format_watchlist,
    format_watchlist_instruments,
])
def test_returns_no_data_for_none(fn):
    assert fn(None) == _NO_DATA


@pytest.mark.parametrize("fn", [
    format_gainers_losers,
    format_most_active,
    format_noii_bars,
    format_watchlist,
])
def test_returns_no_data_for_empty_list(fn):
    assert fn([]) == _NO_DATA


# ---------------------------------------------------------------------------
# Screener: Gainers / Losers
# ---------------------------------------------------------------------------

class TestFormatGainersLosers:
    def test_formats_data_list(self):
        data = {
            "has_more": True,
            "data": [
                {
                    "symbol": "TSLA",
                    "name": "Tesla Inc",
                    "price": "250.00",
                    "pre_close": "235.00",
                    "open": "236.00",
                    "high": "252.00",
                    "low": "234.00",
                    "close": "250.00",
                    "change": "15.00",
                    "change_ratio": "0.064",
                    "amplitude": "0.0766",
                    "volume": "5000000",
                    "turnover_rate": "0.005",
                    "market_value": "800000000000",
                    "exchange_code": "NAS",
                    "currency_code": "USD",
                },
            ],
        }
        result = format_gainers_losers(data)
        assert "Gainers / Losers" in result
        assert "TSLA" in result
        assert "Tesla Inc" in result
        assert "250.00" in result
        assert "235.00" in result
        assert "0.064" in result
        assert "0.0766" in result
        assert "NAS" in result
        assert "More results available" in result

    def test_no_has_more(self):
        data = {"has_more": False, "data": [{"symbol": "X", "name": "Test"}]}
        result = format_gainers_losers(data)
        assert "More results available" not in result

    def test_empty_data_list(self):
        data = {"has_more": False, "data": []}
        result = format_gainers_losers(data)
        assert result == _NO_DATA


# ---------------------------------------------------------------------------
# Screener: Most Active
# ---------------------------------------------------------------------------

class TestFormatMostActive:
    def test_formats_with_relative_volume(self):
        data = {
            "has_more": False,
            "data": [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc",
                    "price": "290.00",
                    "pre_close": "285.00",
                    "open": "286.00",
                    "high": "291.00",
                    "low": "284.00",
                    "close": "290.00",
                    "change": "5.00",
                    "change_ratio": "0.018",
                    "amplitude": "0.0246",
                    "volume": "80000000",
                    "turnover_rate": "0.005",
                    "market_value": "4500000000000",
                    "exchange_code": "NAS",
                    "currency_code": "USD",
                    "relative_volume_10d": "2.35",
                },
            ],
        }
        result = format_most_active(data)
        assert "Most Active" in result
        assert "AAPL" in result
        assert "Relative Volume 10d: 2.35" in result
        assert "0.018" in result
        assert "NAS" in result

    def test_no_relative_volume(self):
        data = {"data": [{"symbol": "X", "name": "Test", "price": "1"}]}
        result = format_most_active(data)
        assert "Relative Volume 10d" not in result


# ---------------------------------------------------------------------------
# Watchlist
# ---------------------------------------------------------------------------

class TestFormatWatchlist:
    def test_formats_watchlist_list(self):
        data = [
            {
                "watchlist_id": "12345",
                "name": "My Tech Stocks",
                "sort": 1,
                "create_time": "2026-01-01T00:00:00Z",
                "update_time": "2026-05-01T00:00:00Z",
            },
            {
                "watchlist_id": "67890",
                "name": "Crypto",
                "sort": 2,
                "create_time": "2026-02-01T00:00:00Z",
                "update_time": "2026-04-01T00:00:00Z",
            },
        ]
        result = format_watchlist(data)
        assert "Watchlists" in result
        assert "My Tech Stocks" in result
        assert "12345" in result
        assert "Crypto" in result
        assert "67890" in result

    def test_single_dict_wrapped(self):
        data = {"watchlist_id": "111", "name": "Solo", "sort": 1}
        result = format_watchlist(data)
        assert "Solo" in result


class TestFormatWatchlistInstruments:
    def test_formats_instruments(self):
        data = {
            "watchlist_id": "12345",
            "instruments": [
                {
                    "instrument_id": "913256135",
                    "symbol": "AAPL",
                    "name": "Apple Inc",
                    "exchange_code": "NSQ",
                    "sort": 1,
                    "added_time": "2026-01-15T10:00:00Z",
                },
                {
                    "instrument_id": "913303964",
                    "symbol": "MSFT",
                    "name": "Microsoft Corp",
                    "exchange_code": "NSQ",
                    "sort": 2,
                    "added_time": "2026-01-16T10:00:00Z",
                },
            ],
        }
        result = format_watchlist_instruments(data)
        assert "12345" in result
        assert "AAPL" in result
        assert "MSFT" in result
        assert "Apple Inc" in result

    def test_empty_instruments(self):
        data = {"watchlist_id": "999", "instruments": []}
        result = format_watchlist_instruments(data)
        assert "No instruments" in result


# ---------------------------------------------------------------------------
# NOII Bars
# ---------------------------------------------------------------------------

class TestFormatNoiiBars:
    def test_formats_bars(self):
        data = [
            {
                "instrument_id": "913256135",
                "symbol": "AAPL",
                "imbalance_time": "1711262998500",
                "imbalance_ref_price": "172.35",
                "imbalance_near_price": "173.10",
                "imbalance_far_price": "175.50",
                "imbalance_action_type": "PRE_OPEN",
            },
        ]
        result = format_noii_bars(data)
        assert "NOII Bars" in result
        assert "AAPL" in result
        assert "172.35" in result
        assert "173.10" in result
        assert "PRE_OPEN" in result

    def test_single_dict_wrapped(self):
        data = {"symbol": "TSLA", "imbalance_ref_price": "250.00"}
        result = format_noii_bars(data)
        assert "TSLA" in result
        assert "250.00" in result


# ---------------------------------------------------------------------------
# NOII Snapshot
# ---------------------------------------------------------------------------

class TestFormatNoiiSnapshot:
    def test_formats_snapshot(self):
        data = {
            "instrument_id": "913256135",
            "symbol": "AAPL",
            "paired_shares": "701859",
            "imbalance_shares": "5715",
            "imbalance_side": "2",
            "imbalance_ref_price": "253.83",
            "imbalance_near_price": "253.93",
            "imbalance_far_price": "253.98",
            "imbalance_action_type": "PRE_OPEN",
            "imbalance_time": "1774272599000",
            "imbalance_var_indicator": "10",
        }
        result = format_noii_snapshot(data)
        assert "NOII Snapshot: AAPL" in result
        assert "701859" in result
        assert "5715" in result
        assert "253.83" in result
        assert "PRE_OPEN" in result

    def test_handles_list_input(self):
        data = [{"symbol": "MSFT", "paired_shares": "100000"}]
        result = format_noii_snapshot(data)
        assert "MSFT" in result
        assert "100000" in result

    def test_empty_list(self):
        assert format_noii_snapshot([]) == _NO_DATA


# ---------------------------------------------------------------------------
# Stock bars start_time/end_time parameter building
# ---------------------------------------------------------------------------

class TestStockBarsKwargsBuilding:
    """Test that _build_kwargs correctly passes start_time/end_time."""

    def test_build_kwargs_includes_start_end_time(self):
        from webull_openapi_mcp.tools.market_data.stock import _build_kwargs

        kwargs = _build_kwargs(
            {"symbol": "AAPL", "category": "US_STOCK", "timespan": "D", "count": "5"},
            start_time=1746662400000,
            end_time=1747267200000,
        )
        assert kwargs["start_time"] == 1746662400000
        assert kwargs["end_time"] == 1747267200000

    def test_build_kwargs_excludes_none_values(self):
        from webull_openapi_mcp.tools.market_data.stock import _build_kwargs

        kwargs = _build_kwargs(
            {"symbol": "AAPL"},
            start_time=None,
            end_time=None,
        )
        assert "start_time" not in kwargs
        assert "end_time" not in kwargs

    def test_build_kwargs_excludes_false_values(self):
        from webull_openapi_mcp.tools.market_data.stock import _build_kwargs

        kwargs = _build_kwargs(
            {"symbol": "AAPL"},
            real_time_required=False,
            start_time=1746662400000,
        )
        assert "real_time_required" not in kwargs
        assert kwargs["start_time"] == 1746662400000
