"""Watchlist tools for Webull MCP Server.

Provides: get_watchlists, create_watchlist, update_watchlist, delete_watchlist,
          get_watchlist_instruments, add_watchlist_instruments,
          remove_watchlist_instruments, update_watchlist_instruments.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from webull_openapi_mcp.errors import handle_sdk_exception
from webull_openapi_mcp.formatters import (
    extract_response_data,
    format_watchlist,
    format_watchlist_instruments,
    prepend_disclaimer,
)

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from webull_openapi_mcp.audit import AuditLogger
    from webull_openapi_mcp.config import ServerConfig
    from webull_openapi_mcp.sdk_client import WebullSDKClient


def register_watchlist_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
) -> None:
    """Register watchlist management tools."""

    @mcp.tool(
        description=(
            "Get all watchlists for the current user. "
            "Returns: watchlist_id, name, sort, create_time, update_time."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_watchlists() -> str:
        """Get all user watchlists sorted by sort order."""
        audit.log_tool_call("get_watchlists", {})
        try:
            data = extract_response_data(sdk.data.watchlist.get_watchlist())
            return prepend_disclaimer(format_watchlist(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_watchlists", config.region_id)

    @mcp.tool(
        description=(
            "Create a new watchlist. Maximum 20 watchlists can be created. "
            "Returns: watchlist_id of the newly created watchlist."
        ),
    )
    async def create_watchlist(
        name: str,
        sort: Optional[int] = None,
    ) -> str:
        """Create a new watchlist.

        Args:
            name: Watchlist name.
            sort: Sort order number (optional).
        """
        audit.log_tool_call("create_watchlist", {"name": name})
        try:
            data = extract_response_data(
                sdk.data.watchlist.create_watchlist(name=name, sort=sort)
            )
            if isinstance(data, dict):
                wid = data.get("watchlist_id") or ""
                return prepend_disclaimer(f"Watchlist created successfully.\nwatchlist_id: {wid}")
            return prepend_disclaimer(f"Watchlist created: {data}")
        except Exception as e:
            return handle_sdk_exception(e, "create_watchlist", config.region_id)

    @mcp.tool(
        description=(
            "Update an existing watchlist's name or sort order. "
            "Only provided fields will be updated."
        ),
    )
    async def update_watchlist(
        watchlist_id: str,
        name: Optional[str] = None,
        sort: Optional[int] = None,
    ) -> str:
        """Update watchlist properties.

        Args:
            watchlist_id: Watchlist unique identifier.
            name: New watchlist name (optional).
            sort: New sort order number (optional).
        """
        audit.log_tool_call("update_watchlist", {"watchlist_id": watchlist_id})
        try:
            data = extract_response_data(
                sdk.data.watchlist.update_watchlist(
                    watchlist_id=watchlist_id, name=name, sort=sort,
                )
            )
            return prepend_disclaimer("Watchlist updated successfully.")
        except Exception as e:
            return handle_sdk_exception(e, "update_watchlist", config.region_id)

    @mcp.tool(
        description=(
            "Delete a watchlist and all instruments in it. "
            "This operation is irreversible."
        ),
    )
    async def delete_watchlist(watchlist_id: str) -> str:
        """Delete a watchlist permanently.

        Args:
            watchlist_id: Watchlist unique identifier.
        """
        audit.log_tool_call("delete_watchlist", {"watchlist_id": watchlist_id})
        try:
            data = extract_response_data(
                sdk.data.watchlist.delete_watchlist(watchlist_id=watchlist_id)
            )
            return prepend_disclaimer("Watchlist deleted successfully.")
        except Exception as e:
            return handle_sdk_exception(e, "delete_watchlist", config.region_id)

    @mcp.tool(
        description=(
            "Get all instruments in a watchlist. "
            "Returns: instrument_id, symbol, name, exchange_code, sort, added_time."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_watchlist_instruments(watchlist_id: str) -> str:
        """Get instruments in a specific watchlist.

        Args:
            watchlist_id: Watchlist unique identifier.
        """
        audit.log_tool_call("get_watchlist_instruments", {"watchlist_id": watchlist_id})
        try:
            data = extract_response_data(
                sdk.data.watchlist.get_instruments(watchlist_id=watchlist_id)
            )
            return prepend_disclaimer(format_watchlist_instruments(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_watchlist_instruments", config.region_id)

    @mcp.tool(
        description=(
            "Add instruments to a watchlist. Maximum 1000 instruments total across all watchlists. "
            "Does not support event contracts, futures, or options."
        ),
    )
    async def add_watchlist_instruments(
        watchlist_id: str,
        instruments: list[dict],
    ) -> str:
        """Add instruments to a watchlist.

        Args:
            watchlist_id: Watchlist unique identifier.
            instruments: List of instruments, each with 'symbol' and 'category'
                (e.g. [{"symbol": "AAPL", "category": "US_STOCK"}]).
        """
        audit.log_tool_call("add_watchlist_instruments", {"watchlist_id": watchlist_id, "count": len(instruments)})
        try:
            data = extract_response_data(
                sdk.data.watchlist.add_instruments(
                    watchlist_id=watchlist_id, instruments=instruments,
                )
            )
            return prepend_disclaimer("Instruments added to watchlist successfully.")
        except Exception as e:
            return handle_sdk_exception(e, "add_watchlist_instruments", config.region_id)

    @mcp.tool(
        description=(
            "Remove instruments from a watchlist by symbol and category."
        ),
    )
    async def remove_watchlist_instruments(
        watchlist_id: str,
        instruments: list[dict],
    ) -> str:
        """Remove instruments from a watchlist.

        Args:
            watchlist_id: Watchlist unique identifier.
            instruments: List of instruments to remove, each with 'symbol' and 'category'
                (e.g. [{"symbol": "AAPL", "category": "US_STOCK"}]).
        """
        audit.log_tool_call("remove_watchlist_instruments", {"watchlist_id": watchlist_id, "count": len(instruments)})
        try:
            data = extract_response_data(
                sdk.data.watchlist.remove_instruments(
                    watchlist_id=watchlist_id, instruments=instruments,
                )
            )
            return prepend_disclaimer("Instruments removed from watchlist successfully.")
        except Exception as e:
            return handle_sdk_exception(e, "remove_watchlist_instruments", config.region_id)

    @mcp.tool(
        description=(
            "Update the sort order of instruments in a watchlist."
        ),
    )
    async def update_watchlist_instruments(
        watchlist_id: str,
        instruments: list[dict],
    ) -> str:
        """Update instrument sort order in a watchlist.

        Args:
            watchlist_id: Watchlist unique identifier.
            instruments: List of instruments with new sort order, each with
                'symbol', 'category', and 'sort'
                (e.g. [{"symbol": "AAPL", "category": "US_STOCK", "sort": 1}]).
        """
        audit.log_tool_call("update_watchlist_instruments", {"watchlist_id": watchlist_id, "count": len(instruments)})
        try:
            data = extract_response_data(
                sdk.data.watchlist.update_instruments(
                    watchlist_id=watchlist_id, instruments=instruments,
                )
            )
            return prepend_disclaimer("Watchlist instruments sort order updated successfully.")
        except Exception as e:
            return handle_sdk_exception(e, "update_watchlist_instruments", config.region_id)
