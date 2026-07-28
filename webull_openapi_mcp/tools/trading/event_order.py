"""Event contract order tools for Webull MCP Server.

Provides fine-grained event contract order tools:
- place_event_order: Place an event contract order
- replace_event_order: Modify existing event contract order

Note: Uses order_v3 SDK API (OrderOperationV3).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from webull_openapi_mcp.errors import ValidationError, handle_sdk_exception
from webull_openapi_mcp.formatters import prepend_disclaimer, extract_response_data, format_decimal
from webull_openapi_mcp.guards import validate_client_order_id
from webull_openapi_mcp.region_config import get_region_config
from webull_openapi_mcp.tools.trading.account import (
    normalize_account_id,
    resolve_account_id,
)

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from webull_openapi_mcp.audit import AuditLogger
    from webull_openapi_mcp.config import ServerConfig
    from webull_openapi_mcp.sdk_client import WebullSDKClient


def _generate_client_order_id() -> str:
    """Generate a unique client order ID if not provided."""
    return str(uuid.uuid4()).replace("-", "")[:32]


def _format_order_result(data: dict) -> str:
    """Format order result to standard format."""
    result = {}
    if "client_order_id" in data:
        result["client_order_id"] = data["client_order_id"]
    if "order_id" in data:
        result["order_id"] = data["order_id"]

    if not result:
        return str(data)

    lines = [f"{k}: {v}" for k, v in result.items()]
    return "\n".join(lines)


def _build_event_order(
    symbol: str,
    side: str,
    order_type: str,
    time_in_force: str,
    quantity: float,
    limit_price: float,
    coid: str,
    event_outcome: str,
) -> dict:
    """Build the event contract order dict for the SDK."""
    order: dict = {
        "combo_type": "NORMAL",
        "instrument_type": "EVENT",
        "market": "US",
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "time_in_force": time_in_force,
        "quantity": format_decimal(quantity),
        "limit_price": format_decimal(limit_price),
        "entrust_type": "QTY",
        "client_order_id": coid,
        "event_outcome": event_outcome,
    }
    return order


def _validate_event_order(
    symbol: str,
    side: str,
    quantity: float,
    event_outcome: str,
    config: ServerConfig,
) -> None:
    """Validate event contract order parameters.

    Checks: side, quantity limits, symbol whitelist, event_outcome.
    """
    if side not in ("BUY", "SELL"):
        raise ValidationError(f"Invalid side '{side}', must be BUY or SELL", field="side")
    if quantity is None or quantity <= 0:
        raise ValidationError(f"quantity must be > 0, got {quantity}", field="quantity")
    if quantity > config.max_order_quantity:
        raise ValidationError(
            f"quantity {quantity} exceeds max_order_quantity {config.max_order_quantity}",
            field="quantity",
        )
    if event_outcome not in ("yes", "no"):
        raise ValidationError(
            f"Invalid event_outcome '{event_outcome}', must be 'yes' or 'no'",
            field="event_outcome",
        )
    if config.symbol_whitelist is not None and symbol not in config.symbol_whitelist:
        raise ValidationError(
            f"Symbol '{symbol}' is not in the allowed whitelist",
            field="symbol",
        )


def register_event_order_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
) -> None:
    """Register event contract order tools."""

    @mcp.tool(
        description=(
            "[US Only] Place an event contract order. LIMIT/DAY only.\n"
            "Account: Events Cash account. Call get_account_list first.\n"
            "event_outcome: Event outcome decision, possible values: yes, no.\n"
            "Returns: {client_order_id, order_id}"
        ),
    )
    async def place_event_order(
        symbol: str,
        side: str,
        quantity: float,
        limit_price: float,
        event_outcome: str,
        account_id: Optional[str] = None,
        client_order_id: Optional[str] = None,
        order_type: str = "LIMIT",
        time_in_force: str = "DAY",
    ) -> str:
        """Place an event contract order."""
        audit.log_tool_call("place_event_order", {"symbol": symbol, "side": side})

        # Validate order parameters
        try:
            _validate_event_order(symbol, side, quantity, event_outcome, config)
        except ValidationError as e:
            audit.log_validation_error("place_event_order", e.message, {
                "symbol": symbol, "side": side, "quantity": quantity,
            })
            return f"Validation error: {e.message}"

        # Auto-resolve account_id
        try:
            region_cfg = get_region_config(config.region_id)
            account_id = await resolve_account_id(sdk, "event", account_id, region_cfg)
        except ValueError as e:
            return f"Account error: {e}"

        try:
            validate_client_order_id(client_order_id)
        except Exception as e:
            return f"Validation error: {e}"

        coid = client_order_id or _generate_client_order_id()

        order = _build_event_order(
            symbol=symbol, side=side, order_type=order_type,
            time_in_force=time_in_force, quantity=quantity,
            limit_price=limit_price, coid=coid, event_outcome=event_outcome,
        )

        audit.log_order_attempt(
            symbol=symbol, side=side, quantity=quantity,
            order_type="EVENT_LIMIT", client_order_id=coid,
            account_id=account_id,
        )

        try:
            response = sdk.trade.order_v3.place_order(
                account_id=account_id, new_orders=[order],
            )
            data = extract_response_data(response)
            audit.log_order_result(
                client_order_id=coid, success=True,
                response=data if isinstance(data, dict) else {},
            )
            return prepend_disclaimer(_format_order_result(data if isinstance(data, dict) else {}))
        except Exception as e:
            audit.log_order_result(
                client_order_id=coid, success=False, response={"error": str(e)},
            )
            return handle_sdk_exception(e, "place_event_order")

    @mcp.tool(
        description=(
            "[US Only] Modify an existing event contract order. "
            "Returns: {client_order_id, order_id}"
        ),
    )
    async def replace_event_order(
        account_id: str,
        client_order_id: str,
        quantity: Optional[float] = None,
        limit_price: Optional[float] = None,
    ) -> str:
        """Modify an existing event contract order."""
        try:
            account_id = normalize_account_id(account_id)
        except ValueError as e:
            return f"Validation error: {e}"
        audit.log_tool_call("replace_event_order", {"account_id": account_id, "client_order_id": client_order_id})

        try:
            validate_client_order_id(client_order_id)
        except Exception as e:
            return f"Validation error: {e}"

        modify_order: dict = {"client_order_id": client_order_id}
        if quantity is not None:
            modify_order["quantity"] = format_decimal(quantity)
        if limit_price is not None:
            modify_order["limit_price"] = format_decimal(limit_price)

        try:
            response = sdk.trade.order_v3.replace_order(
                account_id=account_id, modify_orders=[modify_order],
            )
            data = extract_response_data(response)
            return prepend_disclaimer(_format_order_result(data if isinstance(data, dict) else {}))
        except Exception as e:
            return handle_sdk_exception(e, "replace_event_order")
