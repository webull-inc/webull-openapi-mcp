"""Instrument query tools for Webull MCP Server.

Provides: get_instruments, get_futures_instruments, get_futures_products,
          get_futures_product_class, get_crypto_instruments, get_event_series,
          get_event_instruments, get_event_categories, get_event_events.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional

from webull_openapi_mcp.errors import ValidationError, handle_sdk_exception
from webull_openapi_mcp.guards import (
    validate_enum,
    validate_iso_date,
    validate_pagination_key,
    validate_positive_decimal,
)
from webull_openapi_mcp.formatters import (
    extract_response_data,
    format_event_categories,
    format_event_events,
    format_event_series,
    format_futures_product_classes,
    format_futures_products,
    format_instruments,
    prepend_disclaimer,
)

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from webull_openapi_mcp.audit import AuditLogger
    from webull_openapi_mcp.config import ServerConfig
    from webull_openapi_mcp.sdk_client import WebullSDKClient


def _build_kwargs(base: dict[str, Any], **optional: Any) -> dict[str, Any]:
    """Build kwargs dict, adding only non-None optional values."""
    for key, value in optional.items():
        if value is not None:
            base[key] = value
    return base


def _split_symbols(symbols: str) -> list[str]:
    """Split a comma-separated symbols string into a list."""
    return [s.strip() for s in symbols.split(",") if s.strip()]


def register_instrument_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
) -> None:
    """Register instrument query tools."""
    from webull_openapi_mcp.region_config import get_region_config

    region_config = get_region_config(config.region_id)

    @mcp.tool(
        description=(
            "Get stock/ETF instrument info.\n"
            "Two modes: (1) Query by symbols — pass symbols, no pagination needed. "
            "(2) Query by category — omit symbols, use page_size/last_instrument_id for pagination.\n"
            "category: US_STOCK, HK_STOCK, JP_STOCK, CN_STOCK.\n"
            "sub_category: optional sub-classification filter within the category "
            "(e.g. COMMON_STOCK, ETF, PREFERRED_STOCK, WARRANT, UNITS, RIGHT).\n"
            "status: OC (Tradable), CO (Liquidate only), NT (Non-Tradable).\n"
            "Returns: symbol, name, instrument_type, exchange, sub_category."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_instruments(
        symbols: Optional[str] = None,
        category: str = "US_STOCK",
        sub_category: Optional[str] = None,
        status: Optional[str] = None,
        page_size: int = 1000,
        last_instrument_id: Optional[str] = None,
    ) -> str:
        """Get stock/ETF instrument information. Query by symbols or paginate by category."""
        audit.log_tool_call("get_instruments", {"symbols": symbols, "category": category, "sub_category": sub_category})
        if region_config.region_id in ("jp", "sg") and category not in region_config.valid_instrument_categories:
            return f"Validation error: {region_config.region_id.upper()} region instrument lookup only supports US_STOCK and US_ETF"
        try:
            kwargs = _build_kwargs(
                {"category": category},
                symbols=_split_symbols(symbols) if symbols else None,
                sub_category=sub_category,
                status=status,
                page_size=page_size if page_size != 1000 else None,
                last_instrument_id=last_instrument_id,
            )
            data = extract_response_data(sdk.data.instrument.get_instrument(**kwargs))
            return prepend_disclaimer(format_instruments(data))
        except Exception as e:
            return handle_sdk_exception(e, "get_instruments")

    if region_config.supports_futures:
        # Determine valid futures categories based on region
        _valid_futures_categories = "US_FUTURES, HK_FUTURES" if region_config.region_id == "hk" else "US_FUTURES"

        @mcp.tool(
            description=(
                "Get futures instrument info.\n"
                f"category: {_valid_futures_categories}.\n"
                "Two modes: (1) Query by symbols — pass symbols. "
                "(2) Query by code — pass code.\n"
                "status: OC (Tradable), CO (Liquidate only), NT (Non-Tradable).\n"
                "Returns: symbol, name, instrument_type, exchange."
            ),
            annotations={"readOnlyHint": True},
        )
        async def get_futures_instruments(
            symbols: Optional[str] = None,
            code: Optional[str] = None,
            category: str = "US_FUTURES",
            status: Optional[str] = None,
        ) -> str:
            """Get futures instrument information."""
            audit.log_tool_call("get_futures_instruments", {"symbols": symbols, "code": code, "category": category})
            try:
                kwargs = _build_kwargs(
                    {"category": category},
                    symbols=_split_symbols(symbols) if symbols else None,
                    code=code,
                    status=status,
                )
                data = extract_response_data(
                    sdk.data.instrument.get_futures_instrument(**kwargs)
                )
                return prepend_disclaimer(format_instruments(data))
            except Exception as e:
                return handle_sdk_exception(e, "get_futures_instruments")

        @mcp.tool(
            description=(
                "Get all futures products and product codes.\n"
                f"category: {_valid_futures_categories}.\n"
                "product_class_id: optional filter by product class.\n"
                "Returns: name, code, product_class_id, product_class_name, exchange_code."
            ),
            annotations={"readOnlyHint": True},
        )
        async def get_futures_products(
            category: str = "US_FUTURES",
            product_class_id: Optional[int] = None,
        ) -> str:
            """Get all futures products and their product codes."""
            audit.log_tool_call("get_futures_products", {"category": category})
            try:
                kwargs = _build_kwargs(
                    {"category": category},
                    product_class_id=product_class_id,
                )
                data = extract_response_data(sdk.data.instrument.get_futures_products(**kwargs))
                return prepend_disclaimer(format_futures_products(data))
            except Exception as e:
                return handle_sdk_exception(e, "get_futures_products")

        @mcp.tool(
            description=(
                "Get all futures product classification groups.\n"
                f"category: {_valid_futures_categories}.\n"
                "Returns: product_class_id, product_class_name."
            ),
            annotations={"readOnlyHint": True},
        )
        async def get_futures_product_class(
            category: str = "US_FUTURES",
        ) -> str:
            """Get all futures product classification groups."""
            audit.log_tool_call("get_futures_product_class", {"category": category})
            try:
                data = extract_response_data(sdk.data.instrument.get_futures_product_class(category=category))
                return prepend_disclaimer(format_futures_product_classes(data))
            except Exception as e:
                return handle_sdk_exception(e, "get_futures_product_class")

    if region_config.supports_crypto:
        @mcp.tool(
            description=(
                "Get cryptocurrency instrument info.\n"
                "Two modes: (1) Query by symbols — pass symbols. "
                "(2) Query all — omit symbols, use page_size/last_instrument_id for pagination.\n"
                "category: US_CRYPTO.\n"
                "status: OC (Tradable), CO (Liquidate only), NT (Non-Tradable).\n"
                "Returns: symbol, name, instrument_type, exchange."
            ),
            annotations={"readOnlyHint": True},
        )
        async def get_crypto_instruments(
            symbols: Optional[str] = None,
            category: str = "US_CRYPTO",
            status: Optional[str] = None,
            page_size: int = 1000,
            last_instrument_id: Optional[str] = None,
        ) -> str:
            """Get cryptocurrency instrument information."""
            audit.log_tool_call("get_crypto_instruments", {"symbols": symbols})
            try:
                kwargs = _build_kwargs(
                    {"category": category},
                    symbols=_split_symbols(symbols) if symbols else None,
                    status=status,
                    page_size=page_size if page_size != 1000 else None,
                    last_instrument_id=last_instrument_id,
                )
                data = extract_response_data(sdk.data.instrument.get_crypto_instrument(**kwargs))
                return prepend_disclaimer(format_instruments(data))
            except Exception as e:
                return handle_sdk_exception(e, "get_crypto_instruments")

    if region_config.supports_event_contracts:
        @mcp.tool(
            description=(
                "Get event contract series (recurring event templates).\n"
                "category: ECONOMICS, FINANCIALS, POLITICS, ENTERTAINMENT, "
                "SCIENCE_TECHNOLOGY, CLIMATE_WEATHER, TRANSPORTATION, CRYPTO, SPORTS.\n"
                "Returns: series_id, name, category."
            ),
            annotations={"readOnlyHint": True},
        )
        async def get_event_series(
            symbols: Optional[str] = None,
            category: Optional[str] = None,
            page_size: int = 500,
            last_series_id: Optional[str] = None,
        ) -> str:
            """Get event contract series list."""
            audit.log_tool_call("get_event_series", {})
            try:
                kwargs = _build_kwargs(
                    {},
                    category=category,
                    symbols=_split_symbols(symbols) if symbols else None,
                    page_size=page_size if page_size != 500 else None,
                    last_series_id=last_series_id,
                )
                data = extract_response_data(sdk.data.instrument.get_event_series(**kwargs))
                return prepend_disclaimer(format_event_series(data))
            except Exception as e:
                return handle_sdk_exception(e, "get_event_series")

        @mcp.tool(
            description=(
                "Get event contract instruments by series.\n"
                "expiration_date_after: filter items expiring after date (YYYY-MM-DD, default today).\n"
                "Returns: symbol, name, instrument_type, exchange."
            ),
            annotations={"readOnlyHint": True},
        )
        async def get_event_instruments(
            series_symbol: str,
            event_symbol: Optional[str] = None,
            symbols: Optional[str] = None,
            expiration_date_after: Optional[str] = None,
            page_size: int = 500,
            last_instrument_id: Optional[str] = None,
        ) -> str:
            """Get event contract instrument information."""
            audit.log_tool_call("get_event_instruments", {"series_symbol": series_symbol})
            try:
                kwargs = _build_kwargs(
                    {"series_symbol": series_symbol},
                    event_symbol=event_symbol,
                    symbols=_split_symbols(symbols) if symbols else None,
                    expiration_date_after=expiration_date_after,
                    page_size=page_size if page_size != 500 else None,
                    last_instrument_id=last_instrument_id,
                )
                data = extract_response_data(sdk.data.instrument.get_event_instrument(**kwargs))
                return prepend_disclaimer(format_instruments(data))
            except Exception as e:
                return handle_sdk_exception(e, "get_event_instruments")

        @mcp.tool(
            description=(
                "Get event contract category list. "
                "Returns: category_id, name."
            ),
            annotations={"readOnlyHint": True},
        )
        async def get_event_categories() -> str:
            """Get event contract category list."""
            audit.log_tool_call("get_event_categories", {})
            try:
                data = extract_response_data(sdk.data.instrument.get_event_categories())
                return prepend_disclaimer(format_event_categories(data))
            except Exception as e:
                return handle_sdk_exception(e, "get_event_categories")

        @mcp.tool(
            description=(
                "Get events within a series.\n"
                "status: TRADABLE, EXPIRED, SETTLED.\n"
                "Returns: event_id, name, status, expiration_date."
            ),
            annotations={"readOnlyHint": True},
        )
        async def get_event_events(
            series_symbol: str,
            symbols: Optional[str] = None,
            status: Optional[str] = None,
        ) -> str:
            """Get event contract events list."""
            audit.log_tool_call("get_event_events", {"series_symbol": series_symbol})
            try:
                kwargs = _build_kwargs(
                    {"series_symbol": series_symbol},
                    symbols=_split_symbols(symbols) if symbols else None,
                    status=status,
                )
                data = extract_response_data(sdk.data.instrument.get_event_events(**kwargs))
                return prepend_disclaimer(format_event_events(data))
            except Exception as e:
                return handle_sdk_exception(e, "get_event_events")

    if region_config.supports_options:
        @mcp.tool(
            description=(
                "List US-listed option contracts using the current cursor protocol.\n"
                "category: US_OPTION only. option_symbols/underlying_symbols: comma-separated filters.\n"
                "status: LISTING or DELISTING. option_type: CALL or PUT.\n"
                "style: AMERICAN or EUROPEAN.\n"
                "start_date: exact expiration date to match (YYYY-MM-DD).\n"
                "end_date: inclusive lower bound of the expiration date (YYYY-MM-DD).\n"
                "pagination_key: previous-page cursor.\n"
                "Returns contract identifiers, terms, exchanges, deliverables, and the next cursor."
            ),
            annotations={"readOnlyHint": True},
        )
        async def get_option_contracts(
            category: str = "US_OPTION",
            option_symbols: Optional[str] = None,
            underlying_symbols: Optional[str] = None,
            status: Optional[str] = None,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            root_symbol: Optional[str] = None,
            option_type: Optional[str] = None,
            style: Optional[str] = None,
            strike_price_gte: Optional[str] = None,
            strike_price_lte: Optional[str] = None,
            ppind: Optional[bool] = None,
            show_deliverables: Optional[bool] = None,
            pagination_key: Optional[str] = None,
        ) -> str:
            """List option contracts using the list_option_contracts cursor endpoint."""
            audit.log_tool_call(
                "get_option_contracts",
                {"option_symbols": option_symbols, "underlying_symbols": underlying_symbols},
            )
            try:
                validate_enum(category, frozenset({"US_OPTION"}), "category")
                validate_enum(status, frozenset({"LISTING", "DELISTING"}), "status")
                validate_enum(option_type, frozenset({"CALL", "PUT"}), "option_type")
                validate_enum(style, frozenset({"AMERICAN", "EUROPEAN"}), "style")
                validate_iso_date(start_date, "start_date")
                validate_iso_date(end_date, "end_date")
                validate_pagination_key(pagination_key)
                if strike_price_gte is not None:
                    validate_positive_decimal(strike_price_gte, "strike_price_gte")
                if strike_price_lte is not None:
                    validate_positive_decimal(strike_price_lte, "strike_price_lte")
                if strike_price_gte is not None and strike_price_lte is not None:
                    if Decimal(str(strike_price_gte)) > Decimal(str(strike_price_lte)):
                        raise ValidationError(
                            "strike_price_gte must not exceed strike_price_lte",
                            field="strike_price_gte",
                        )
            except ValidationError as e:
                return f"Validation error: {e.message}"

            try:
                kwargs = _build_kwargs(
                    {"category": category},
                    option_symbols=option_symbols,
                    underlying_symbols=underlying_symbols,
                    status=status,
                    start_date=start_date,
                    end_date=end_date,
                    root_symbol=root_symbol,
                    option_type=option_type,
                    style=style,
                    strike_price_gte=strike_price_gte,
                    strike_price_lte=strike_price_lte,
                    ppind=ppind,
                    show_deliverables=show_deliverables,
                    pagination_key=pagination_key,
                )
                data = extract_response_data(sdk.data.instrument.list_option_contracts(**kwargs))
                return prepend_disclaimer(_format_option_contracts(data))
            except Exception as e:
                return handle_sdk_exception(e, "get_option_contracts")


def _format_option_contracts(data) -> str:
    """Format option contracts and preserve pagination and deliverables."""
    if not data:
        return "No option contracts found."

    pagination_key = None
    contracts = data
    if isinstance(data, dict):
        pagination_key = data.get("pagination_key") or data.get("next_pagination_key")
        # Presence-aware extraction: an empty list [] is a valid "no results"
        # response, so check key presence instead of truthiness. Falling back to
        # [data] only when no contracts key exists avoids wrapping an empty
        # envelope as a fake all-N/A contract (API-1957).
        nested = None
        for key in ("data", "items", "result"):
            if key in data:
                nested = data.get(key)
                break
        contracts = nested if isinstance(nested, list) else [data]
    if not isinstance(contracts, list):
        return str(data)

    # Defensive filter: drop junk records with no real instrument_id so a
    # backend-returned all-null record is never shown as a contract (API-1957).
    contracts = [
        item for item in contracts
        if not isinstance(item, dict) or item.get("instrument_id")
    ]
    if not contracts:
        return "No option contracts found."

    lines = [f"=== Option Contracts ({len(contracts)} results) ==="]
    for item in contracts:
        if not isinstance(item, dict):
            lines.append(f"  {item}")
            continue
        lines.append(
            f"  Symbol: {item.get('symbol', 'N/A')}  "
            f"Instrument ID: {item.get('instrument_id', 'N/A')}  "
            f"Underlying: {item.get('underlying_symbol', 'N/A')}  "
            f"Type: {item.get('option_type', 'N/A')}"
        )
        lines.append(
            f"    Strike: {item.get('strike_price', 'N/A')}  "
            f"Expiration: {item.get('init_exp_date', item.get('expiration_date', 'N/A'))}  "
            f"Style: {item.get('style', 'N/A')}  "
            f"Status: {item.get('status', 'N/A')}  "
            f"Tradable Status: {item.get('tradable_status', 'N/A')}"
        )
        for field in (
            "root_symbol", "underlying_instrument_id", "underlying_type",
            "multiplier", "settlement_method", "expired_cycle", "ppind",
            "currency", "def_type", "listed_exchanges",
        ):
            if field in item:
                lines.append(f"    {field.replace('_', ' ').title()}: {item[field]}")
        deliverables = item.get("deliverables") or []
        if isinstance(deliverables, list) and deliverables:
            lines.append("    Deliverables:")
            for deliverable in deliverables:
                lines.append(f"      {deliverable}")
    if pagination_key:
        lines.append(f"\nNext pagination_key: {pagination_key}")
    return "\n".join(lines)
