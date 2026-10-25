"""Regression tests for get_order_history outgoing timestamp normalization.

API-1958: the backend requires millisecond-precision UTC timestamps
(e.g. 2026-10-01T00:00:00.000Z) and rejects second-precision input
(e.g. 2026-10-01T00:00:00Z) with HTTP 417. The tool stays lenient and accepts
both forms, but must normalize second-precision input to millisecond form on
the OUTGOING request so the backend accepts it.
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from webull_openapi_mcp.tools.trading import order as order_tools


class _ToolRegistry:
    """Minimal FastMCP stand-in that captures registered tool callables."""

    def __init__(self) -> None:
        self.tools: dict = {}

    def tool(self, *args, **kwargs):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def _register_order_history():
    """Register order tools against a stub SDK and return the tool + SDK mock."""
    registry = _ToolRegistry()
    sdk = MagicMock()
    sdk.trade.order_v3.list_order_history.return_value = {"orders": []}
    audit = MagicMock()
    order_tools.register_order_tools(registry, sdk, audit)
    return registry.tools["get_order_history"], sdk


def _sent_kwargs(sdk) -> dict:
    sdk.trade.order_v3.list_order_history.assert_called_once()
    return sdk.trade.order_v3.list_order_history.call_args.kwargs


def test_second_precision_start_time_sent_as_milliseconds():
    get_order_history, sdk = _register_order_history()

    asyncio.run(get_order_history(account_id="acc-1", start_time="2026-10-01T00:00:00Z"))

    assert _sent_kwargs(sdk)["start_time"] == "2026-10-01T00:00:00.000Z"


def test_second_precision_end_time_sent_as_milliseconds():
    get_order_history, sdk = _register_order_history()

    asyncio.run(get_order_history(account_id="acc-1", end_time="2026-10-02T00:00:00Z"))

    assert _sent_kwargs(sdk)["end_time"] == "2026-10-02T00:00:00.000Z"


def test_second_precision_both_times_sent_as_milliseconds():
    get_order_history, sdk = _register_order_history()

    asyncio.run(
        get_order_history(
            account_id="acc-1",
            start_time="2026-10-01T00:00:00Z",
            end_time="2026-10-02T00:00:00Z",
        )
    )

    sent = _sent_kwargs(sdk)
    assert sent["start_time"] == "2026-10-01T00:00:00.000Z"
    assert sent["end_time"] == "2026-10-02T00:00:00.000Z"


def test_millisecond_input_passes_through_without_double_append():
    get_order_history, sdk = _register_order_history()

    asyncio.run(
        get_order_history(
            account_id="acc-1",
            start_time="2026-10-01T00:00:00.000Z",
            end_time="2026-10-02T12:34:56.123Z",
        )
    )

    sent = _sent_kwargs(sdk)
    assert sent["start_time"] == "2026-10-01T00:00:00.000Z"
    assert sent["end_time"] == "2026-10-02T12:34:56.123Z"
    assert sent["start_time"].count(".") == 1
    assert sent["end_time"].count(".") == 1
