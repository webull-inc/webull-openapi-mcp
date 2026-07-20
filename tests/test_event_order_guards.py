"""Unit tests for event contract order validation."""

from __future__ import annotations

import pytest

from webull_openapi_mcp.config import ServerConfig
from webull_openapi_mcp.errors import ValidationError
from webull_openapi_mcp.tools.trading.event_order import _validate_event_order


def _config(**overrides) -> ServerConfig:
    defaults = dict(
        app_key="test_key",
        app_secret="test_secret",
        region_id="us",
        max_order_notional_usd=10_000.0,
        max_order_quantity=1_000.0,
    )
    defaults.update(overrides)
    return ServerConfig(**defaults)


def _validate(**overrides) -> None:
    base = dict(
        symbol="TRUMP2028",
        side="BUY",
        quantity=10,
        limit_price=0.50,
        event_outcome="yes",
        order_type="LIMIT",
        time_in_force="DAY",
        config=_config(),
    )
    base.update(overrides)
    return _validate_event_order(**base)


def test_valid_order_allowed():
    _validate()


def test_invalid_side_rejected():
    with pytest.raises(ValidationError) as exc_info:
        _validate(side="SHORT")
    assert exc_info.value.field == "side"


def test_invalid_order_type_rejected():
    with pytest.raises(ValidationError) as exc_info:
        _validate(order_type="MARKET")
    assert exc_info.value.field == "order_type"


def test_invalid_time_in_force_rejected():
    with pytest.raises(ValidationError) as exc_info:
        _validate(time_in_force="GTC")
    assert exc_info.value.field == "time_in_force"


def test_zero_quantity_rejected():
    with pytest.raises(ValidationError) as exc_info:
        _validate(quantity=0)
    assert exc_info.value.field == "quantity"


def test_quantity_exceeding_max_rejected():
    with pytest.raises(ValidationError) as exc_info:
        _validate(quantity=1001, config=_config(max_order_quantity=1000))
    assert exc_info.value.field == "quantity"


def test_notional_exceeding_max_rejected():
    with pytest.raises(ValidationError) as exc_info:
        _validate(
            quantity=100, limit_price=15.0,
            config=_config(max_order_notional_usd=1_000.0),
        )
    assert exc_info.value.field == "notional"


def test_notional_within_max_allowed():
    _validate(
        quantity=100, limit_price=5.0,
        config=_config(max_order_notional_usd=1_000.0),
    )


def test_invalid_event_outcome_rejected():
    with pytest.raises(ValidationError) as exc_info:
        _validate(event_outcome="maybe")
    assert exc_info.value.field == "event_outcome"


def test_symbol_not_in_whitelist_rejected():
    with pytest.raises(ValidationError) as exc_info:
        _validate(config=_config(symbol_whitelist=["OTHER"]))
    assert exc_info.value.field == "symbol"
