"""Unit tests for instrument tools (company profile, analyst rating, analyst target price)."""

from __future__ import annotations

import pytest

from webull_openapi_mcp.formatters import (
    format_analyst_rating,
    format_analyst_target_price,
    format_company_profile,
)


_NO_DATA = "No data available."


# ---------------------------------------------------------------------------
# Empty / None data handling
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fn", [
    format_company_profile,
    format_analyst_rating,
    format_analyst_target_price,
])
def test_returns_no_data_for_none(fn):
    assert fn(None) == _NO_DATA


@pytest.mark.parametrize("fn", [
    format_company_profile,
    format_analyst_rating,
    format_analyst_target_price,
])
def test_returns_no_data_for_empty_dict(fn):
    assert fn({}) == _NO_DATA


# ---------------------------------------------------------------------------
# Company Profile
# ---------------------------------------------------------------------------

class TestFormatCompanyProfile:
    def test_formats_basic_fields(self):
        data = {
            "symbol": "AAPL",
            "company_name": "Apple Inc",
            "exhibition_code": "NASDAQ",
            "ceo": "Tim Cook",
            "employees": "164000",
            "establish_date": "1977-04-01",
            "address": "One Apple Park Way, Cupertino, CA",
            "industries": ["Consumer Electronics", "Technology"],
            "profile": "Apple designs and manufactures consumer electronics.",
        }
        result = format_company_profile(data)
        assert "AAPL" in result
        assert "Apple Inc" in result
        assert "NASDAQ" in result
        assert "Tim Cook" in result
        assert "164000" in result
        assert "Consumer Electronics" in result
        assert "Apple designs" in result

    def test_handles_missing_optional_fields(self):
        data = {"symbol": "TSLA"}
        result = format_company_profile(data)
        assert "TSLA" in result
        assert "N/A" in result

    def test_industries_as_string(self):
        data = {"symbol": "X", "industries": "Mining"}
        result = format_company_profile(data)
        assert "Mining" in result

    def test_no_profile_description(self):
        data = {"symbol": "GOOG", "company_name": "Alphabet"}
        result = format_company_profile(data)
        assert "Description" not in result

    def test_non_dict_returns_no_data(self):
        assert format_company_profile("invalid") == _NO_DATA
        assert format_company_profile([]) == _NO_DATA


# ---------------------------------------------------------------------------
# Analyst Rating
# ---------------------------------------------------------------------------

class TestFormatAnalystRating:
    def test_formats_all_fields(self):
        data = {
            "symbol": "NVDA",
            "number": "58",
            "strong_buy": "43",
            "buy": "11",
            "hold": "4",
            "sell": "0",
            "under_perform": "0",
            "effective_start_date": "2021-12-29",
        }
        result = format_analyst_rating(data)
        assert "NVDA" in result
        assert "58" in result
        assert "43" in result
        assert "11" in result
        assert "4" in result
        assert "2021-12-29" in result

    def test_handles_missing_fields(self):
        data = {"symbol": "AAPL", "number": "47"}
        result = format_analyst_rating(data)
        assert "AAPL" in result
        assert "47" in result
        assert "N/A" in result

    def test_non_dict_returns_no_data(self):
        assert format_analyst_rating("invalid") == _NO_DATA
        assert format_analyst_rating([]) == _NO_DATA


# ---------------------------------------------------------------------------
# Analyst Target Price
# ---------------------------------------------------------------------------

class TestFormatAnalystTargetPrice:
    def test_formats_all_fields(self):
        data = {
            "symbol": "AAPL",
            "mean": "226.18",
            "low": "170",
            "high": "300",
            "median": "220",
            "currency": "USD",
            "effective_start_date": "2024-01-01",
        }
        result = format_analyst_target_price(data)
        assert "AAPL" in result
        assert "226.18" in result
        assert "170" in result
        assert "300" in result
        assert "220" in result
        assert "USD" in result
        assert "2024-01-01" in result

    def test_handles_missing_fields(self):
        data = {"symbol": "TSLA"}
        result = format_analyst_target_price(data)
        assert "TSLA" in result
        assert "N/A" in result

    def test_non_dict_returns_no_data(self):
        assert format_analyst_target_price("invalid") == _NO_DATA
        assert format_analyst_target_price([]) == _NO_DATA
