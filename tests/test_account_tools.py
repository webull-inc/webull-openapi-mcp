"""Unit tests for account resolution helpers."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from webull_openapi_mcp.tools.trading.account import (
    normalize_account_id,
    resolve_account,
    resolve_account_id,
)


def _sdk_with_accounts(accounts: list[dict]) -> MagicMock:
    sdk = MagicMock()
    sdk.trade.account_v2.get_account_list.return_value = accounts
    return sdk


def test_resolve_account_returns_account_object_for_explicit_id():
    sdk = _sdk_with_accounts([
        {"account_id": "cash-1", "account_type": "CASH", "account_class": "INDIVIDUAL_CASH", "account_label": "Individual Cash"},
        {"account_id": "margin-1", "account_type": "US_MARGIN", "account_class": "INDIVIDUAL_MARGIN", "account_label": "Individual Margin"},
    ])

    account = asyncio.run(resolve_account(sdk, "stock", "margin-1"))

    assert account["account_id"] == "margin-1"
    assert account["account_type"] == "US_MARGIN"
    assert account["account_class"] == "INDIVIDUAL_MARGIN"


def test_normalize_account_id_accepts_string():
    assert normalize_account_id("1227316039148052480") == "1227316039148052480"


def test_normalize_account_id_rejects_int():
    with pytest.raises(ValueError, match="account_id must be a string"):
        normalize_account_id(1227316039148052500)


def test_normalize_account_id_rejects_bool():
    with pytest.raises(ValueError, match="account_id must be a string"):
        normalize_account_id(True)


def test_resolve_account_id_preserves_existing_api():
    sdk = _sdk_with_accounts([
        {"account_id": "cash-1", "account_type": "CASH", "account_class": "INDIVIDUAL_CASH", "account_label": "Individual Cash"},
    ])

    account_id = asyncio.run(resolve_account_id(sdk, "stock"))

    assert account_id == "cash-1"


def test_resolve_account_accepts_numeric_explicit_id():
    sdk = _sdk_with_accounts([
        {
            "account_id": "1227316039148052480",
            "account_type": "CASH",
            "account_class": "INDIVIDUAL_CASH",
            "account_label": "Individual Cash",
        },
    ])

    account = asyncio.run(resolve_account(sdk, "stock", "1227316039148052480"))

    assert account["account_id"] == "1227316039148052480"


def test_resolve_account_returns_placeholder_for_unknown_explicit_id():
    sdk = _sdk_with_accounts([
        {"account_id": "cash-1", "account_type": "CASH", "account_class": "INDIVIDUAL_CASH", "account_label": "Individual Cash"},
        {"account_id": "margin-1", "account_type": "US_MARGIN", "account_class": "INDIVIDUAL_MARGIN", "account_label": "Individual Margin"},
    ])

    account = asyncio.run(resolve_account(sdk, "stock", "missing-1"))

    assert account == {"account_id": "missing-1"}


def test_resolve_account_returns_placeholder_for_unknown_numeric_explicit_id():
    sdk = _sdk_with_accounts([
        {"account_id": "cash-1", "account_type": "CASH", "account_class": "INDIVIDUAL_CASH", "account_label": "Individual Cash"},
    ])

    account = asyncio.run(resolve_account(sdk, "stock", "1227316039148052480"))

    assert account == {"account_id": "1227316039148052480"}


def test_resolve_account_does_not_replace_unknown_explicit_id_with_single_account():
    sdk = _sdk_with_accounts([
        {"account_id": "cash-1", "account_type": "CASH", "account_class": "INDIVIDUAL_CASH", "account_label": "Individual Cash"},
    ])

    account = asyncio.run(resolve_account(sdk, "stock", "missing-1"))

    assert account == {"account_id": "missing-1"}


def test_resolve_account_rejects_ambiguous_auto_selection():
    from webull_openapi_mcp.region_config import US_REGION_CONFIG

    sdk = _sdk_with_accounts([
        {"account_id": "cash-1", "account_type": "CASH", "account_class": "INDIVIDUAL_CASH", "account_label": "Individual Cash"},
        {"account_id": "margin-1", "account_type": "US_MARGIN", "account_class": "INDIVIDUAL_MARGIN", "account_label": "Individual Margin"},
    ])

    with pytest.raises(ValueError, match="Multiple stock accounts"):
        asyncio.run(resolve_account(sdk, "stock", region_config=US_REGION_CONFIG))
