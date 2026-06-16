"""Webull MCP Server — FastMCP implementation.

Builds MCP tools using FastMCP decorators with Webull OpenAPI Python SDK as backend.
Tools are registered based on region configuration and toolset filtering.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP

from webull_openapi_mcp.config import ServerConfig
from webull_openapi_mcp.sdk_client import WebullSDKClient
from webull_openapi_mcp.audit import AuditLogger

logger = logging.getLogger(__name__)


def build_server(config: ServerConfig) -> FastMCP:
    """Construct the Webull MCP server with all tools registered."""
    from webull_openapi_mcp.region_config import get_region_config
    from webull_openapi_mcp.formatters import set_disclaimer_region

    region_config = get_region_config(config.region_id)
    set_disclaimer_region(config.region_id)

    # SDK client and audit logger — initialized in lifespan
    sdk_client = WebullSDKClient(config)
    audit = AuditLogger(config)

    @asynccontextmanager
    async def lifespan(_server: FastMCP) -> AsyncIterator[dict]:
        """Initialize SDK on startup, cleanup on shutdown."""
        from webull_openapi_mcp.sdk_client import TwoFactorAuthRequiredError
        try:
            sdk_client.initialize()
            logger.info("SDK initialized: region=%s, env=%s", config.region_id, config.environment)
        except TwoFactorAuthRequiredError as e:
            import sys
            print(f"\n{'=' * 60}", file=sys.stderr)
            print("MCP SERVER STARTUP FAILED", file=sys.stderr)
            print(f"{'=' * 60}", file=sys.stderr)
            print(f"\n{e}\n", file=sys.stderr)
            print(f"{'=' * 60}\n", file=sys.stderr)
            sys.stderr.flush()
            raise RuntimeError(
                "2FA verification required. Check Webull app to approve, then restart."
            ) from e

        yield {"sdk": sdk_client, "audit": audit, "config": config}

    mcp = FastMCP(
        "Webull OpenAPI MCP",
        lifespan=lifespan,
    )

    # Register tools based on region and toolset config
    _register_tools(mcp, sdk_client, audit, config, region_config)

    logger.info(
        "Built Webull OpenAPI MCP Server: region=%s, toolsets=%s",
        region_config.region_id,
        config.toolsets or "all",
    )

    return mcp


def _is_toolset_enabled(config: ServerConfig, name: str) -> bool:
    return config.toolsets is None or name in config.toolsets


def _register_tools(
    mcp: FastMCP,
    sdk: WebullSDKClient,
    audit: AuditLogger,
    config: ServerConfig,
    region_config: Any,
) -> None:
    """Register all tools based on region and toolset filtering."""
    from webull_openapi_mcp.tools import register_account_tools
    from webull_openapi_mcp.tools import register_assets_tools
    from webull_openapi_mcp.tools import register_order_tools
    from webull_openapi_mcp.tools import register_instrument_tools
    from webull_openapi_mcp.tools import register_stock_market_data_tools
    from webull_openapi_mcp.tools import register_stock_order_tools
    from webull_openapi_mcp.tools import register_option_single_tools
    from webull_openapi_mcp.tools import register_fundamental_tools
    from webull_openapi_mcp.tools import register_extended_fundamental_tools
    from webull_openapi_mcp.tools import register_financial_tools

    # Account tools
    if _is_toolset_enabled(config, "account"):
        register_account_tools(mcp, sdk, audit)
        register_assets_tools(mcp, sdk, audit, config)

    # Instrument tools
    if _is_toolset_enabled(config, "instrument"):
        register_instrument_tools(mcp, sdk, audit, config)
        # Fundamental data (company profile, analyst ratings) — all regions
        register_fundamental_tools(mcp, sdk, audit, config)
        # Stock & fund fundamentals + financial statements — US / HK / JP only
        if region_config.supports_fundamentals:
            register_extended_fundamental_tools(mcp, sdk, audit, config)
            register_financial_tools(mcp, sdk, audit, config)

    # Market data tools
    if _is_toolset_enabled(config, "market-data"):
        register_stock_market_data_tools(mcp, sdk, audit, config)

        # Screener tools (gainers/losers, most active)
        from webull_openapi_mcp.tools import register_screener_tools
        register_screener_tools(mcp, sdk, audit, config)

        # Extended screener (market sectors, high dividend, 52-week high/low) — US / HK / JP only
        if region_config.supports_fundamentals:
            from webull_openapi_mcp.tools import register_extended_screener_tools
            register_extended_screener_tools(mcp, sdk, audit, config)

        # Watchlist tools
        from webull_openapi_mcp.tools import register_watchlist_tools
        register_watchlist_tools(mcp, sdk, audit, config)

        if region_config.supports_futures:
            from webull_openapi_mcp.tools import register_futures_market_data_tools
            register_futures_market_data_tools(mcp, sdk, audit, config)

        if region_config.supports_crypto:
            from webull_openapi_mcp.tools import register_crypto_market_data_tools
            register_crypto_market_data_tools(mcp, sdk, audit, config)

        if region_config.supports_event_contracts:
            from webull_openapi_mcp.tools import register_event_market_data_tools
            register_event_market_data_tools(mcp, sdk, audit, config)

    # Trading tools (includes order query, place, replace, cancel)
    if _is_toolset_enabled(config, "trading"):
        register_order_tools(mcp, sdk, audit)
        register_stock_order_tools(mcp, sdk, audit, config)
        if region_config.supports_options:
            register_option_single_tools(mcp, sdk, audit, config)

        if region_config.supports_combo_orders:
            from webull_openapi_mcp.tools import register_combo_order_tools
            register_combo_order_tools(mcp, sdk, audit, config)

        if region_config.supports_option_strategies:
            from webull_openapi_mcp.tools import register_option_strategy_tools
            register_option_strategy_tools(mcp, sdk, audit, config)

        if region_config.supports_algo_orders:
            from webull_openapi_mcp.tools import register_algo_order_tools
            register_algo_order_tools(mcp, sdk, audit, config)

        if region_config.supports_futures:
            from webull_openapi_mcp.tools import register_futures_order_tools
            register_futures_order_tools(mcp, sdk, audit, config)

        if region_config.supports_crypto:
            from webull_openapi_mcp.tools import register_crypto_order_tools
            register_crypto_order_tools(mcp, sdk, audit, config)

        if region_config.supports_event_contracts:
            from webull_openapi_mcp.tools import register_event_order_tools
            register_event_order_tools(mcp, sdk, audit, config)
