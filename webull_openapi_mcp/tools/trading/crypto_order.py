"""Crypto order tools for Webull MCP Server.

Provides fine-grained crypto order tools:
- place_crypto_order: Place a cryptocurrency order

Note: Crypto does NOT support replace order.
Note: Uses order_v3 SDK API (OrderOperationV3).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from webull_openapi_mcp.errors import ValidationError, handle_sdk_exception
from webull_openapi_mcp.formatters import prepend_disclaimer, extract_response_data
from webull_openapi_mcp.guards import validate_client_order_id, validate_stock_order
from webull_openapi_mcp.tools.trading.account import resolve_account_id

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


def _build_crypto_order(
    symbol: str,
    side: str,
    order_type: str,
    time_in_force: str,
    entrust_type: str,
    coid: str,
    quantity: float | None,
    total_cash_amount: float | None,
    limit_price: float | None,
    stop_price: float | None,
) -> dict:
    """Build the crypto order dict for the SDK."""
    order: dict = {
        "combo_type": "NORMAL",
        "instrument_type": "CRYPTO",
        "market": "US",
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "time_in_force": time_in_force,
        "entrust_type": entrust_type,
        "client_order_id": coid,
    }

    if entrust_type == "AMOUNT" and total_cash_amount is not None:
        order["total_cash_amount"] = str(total_cash_amount)
    elif quantity is not None:
        order["quantity"] = str(quantity)

    if limit_price is not None:
        order["limit_price"] = str(limit_price)
    if stop_price is not None:
        order["stop_price"] = str(stop_price)

    return order


def register_crypto_order_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
) -> None:
    """Register crypto order tools."""

    @mcp.tool(
        description=(
            "[US Only] Place a cryptocurrency order. Supports QTY and AMOUNT. "
            "No replace supported. Min position $2.\n"
            "Account: Crypto account. Call get_account_list first.\n"
            "order_type: MARKET (tif=IOC), LIMIT (tif=DAY/GTC), STOP_LOSS_LIMIT (tif=DAY/GTC).\n"
            "Returns: {client_order_id, order_id}"
        ),
    )
    async def place_crypto_order(
        symbol: str,
        side: str,
        order_type: str,
        time_in_force: str,
        account_id: Optional[str] = None,
        client_order_id: Optional[str] = None,
        entrust_type: str = "QTY",
        quantity: Optional[float] = None,
        total_cash_amount: Optional[float] = None,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> str:
        """Place a cryptocurrency order."""
        audit.log_tool_call("place_crypto_order", {"symbol": symbol, "side": side})

        # Auto-resolve account_id
        try:
            account_id = await resolve_account_id(sdk, "crypto", account_id)
        except ValueError as e:
            return f"Account error: {e}"

        try:
            validate_client_order_id(client_order_id)
        except Exception as e:
            return f"Validation error: {e}"

        # Crypto time_in_force rules: MARKET must use IOC, and IOC is only for MARKET
        if order_type == "MARKET" and time_in_force != "IOC":
            return "Validation error: crypto MARKET orders require time_in_force=IOC"
        if time_in_force == "IOC" and order_type != "MARKET":
            return "Validation error: time_in_force=IOC is only supported for crypto MARKET orders"

        params: dict = {
            "side": side, "order_type": order_type, "time_in_force": time_in_force,
            "quantity": quantity, "symbol": symbol, "entrust_type": entrust_type,
            "total_cash_amount": total_cash_amount,
        }
        if limit_price is not None:
            params["limit_price"] = limit_price
        try:
            validate_stock_order(params, config)
        except ValidationError as e:
            return f"Validation error: {e.message}"

        coid = client_order_id or _generate_client_order_id()

        order = _build_crypto_order(
            symbol=symbol, side=side, order_type=order_type,
            time_in_force=time_in_force, entrust_type=entrust_type, coid=coid,
            quantity=quantity, total_cash_amount=total_cash_amount,
            limit_price=limit_price, stop_price=stop_price,
        )

        audit.log_order_attempt(
            symbol=symbol, side=side,
            quantity=quantity or total_cash_amount or 0,
            order_type=order_type, client_order_id=coid,
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
            return handle_sdk_exception(e, "place_crypto_order")
