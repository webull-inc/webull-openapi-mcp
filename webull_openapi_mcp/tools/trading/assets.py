"""Assets tools for Webull MCP Server.

Provides: get_account_balance, get_account_positions, get_account_position_details (JP only).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from webull_openapi_mcp.errors import ValidationError, handle_sdk_exception
from webull_openapi_mcp.guards import validate_pagination_key
from webull_openapi_mcp.formatters import (
    extract_response_data,
    format_account_balance,
    format_position_details,
    format_positions,
    prepend_disclaimer,
)
from webull_openapi_mcp.tools.trading.account import normalize_account_id

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from webull_openapi_mcp.audit import AuditLogger
    from webull_openapi_mcp.config import ServerConfig
    from webull_openapi_mcp.sdk_client import WebullSDKClient


def register_assets_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
) -> None:
    """Register account balance and position tools."""

    @mcp.tool(
        description=(
            "Get account balance. "
            "Returns: net_liquidation, buying_power, cash_balance, "
            "market_value, unrealized_pnl, realized_pnl."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_account_balance(account_id: str) -> str:
        """Get account balance information."""
        try:
            account_id = normalize_account_id(account_id)
        except ValueError as e:
            return f"Validation error: {e}"
        audit.log_tool_call("get_account_balance", {"account_id": account_id})
        try:
            response = sdk.trade.account_v2.get_account_balance(account_id)
            data = extract_response_data(response)
            return prepend_disclaimer(format_account_balance(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_account_balance")

    @mcp.tool(
        description=(
            "Get account positions, including option strategy legs when present. "
            "Returns position identifiers, symbols, quantities, prices, P&L, and option legs."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_account_positions(account_id: str) -> str:
        """Get account positions list."""
        try:
            account_id = normalize_account_id(account_id)
        except ValueError as e:
            return f"Validation error: {e}"
        audit.log_tool_call("get_account_positions", {"account_id": account_id})
        try:
            response = sdk.trade.account_v2.get_account_position(account_id)
            data = extract_response_data(response)
            return prepend_disclaimer(format_positions(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_account_positions")

    if config.region_id == "jp":
        @mcp.tool(
            description=(
                "[JP Only] Get account position details by instrument_id. "
                "Returns JP contract-level position details with pagination support."
            ),
            annotations={"readOnlyHint": True},
        )
        async def get_account_position_details(
            account_id: str,
            instrument_id: str,
            pagination_key: str | None = None,
        ) -> str:
            """Get JP account position details using the list_position_details cursor endpoint."""
            try:
                account_id = normalize_account_id(account_id)
                validate_pagination_key(pagination_key)
            except (ValueError, ValidationError) as e:
                message = e.message if isinstance(e, ValidationError) else str(e)
                return f"Validation error: {message}"
            audit.log_tool_call(
                "get_account_position_details",
                {"account_id": account_id, "instrument_id": instrument_id},
            )
            try:
                response = sdk.trade.account_v2.list_position_details(
                    account_id=account_id,
                    instrument_id=instrument_id,
                    pagination_key=pagination_key,
                )
                data = extract_response_data(response)
                return prepend_disclaimer(format_position_details(data))
            except Exception as e:
                return handle_sdk_exception(e, "get_account_position_details")
