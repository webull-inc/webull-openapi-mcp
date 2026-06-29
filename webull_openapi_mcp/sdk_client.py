"""Webull SDK adapter layer — single bridge between MCP Server and Webull SDK."""

from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING

from webull.core.client import ApiClient
from webull.core.common.api_type import DEFAULT, QUOTES, EVENTS
from webull.core.exception.exceptions import ClientException, ServerException
from webull.data.data_client import DataClient
from webull.trade.trade_client import TradeClient

if TYPE_CHECKING:
    from webull_openapi_mcp.config import ServerConfig

# Region-specific 2FA documentation links
_2FA_GUIDE_LINKS: dict[str, str] = {
    "br": "https://developer.webull.com.br/apis/docs/authentication/token",
    "hk": "https://developer.webull.hk/apis/docs/authentication/token",
    "jp": "https://developer.webull.co.jp/apis/docs/authentication/token",
    "mx": "https://developer.webull.com.mx/apis/docs/authentication/token",
    "my": "https://developer.webull.com.my/apis/docs/authentication/token",
    "sg": "https://developer.webull.com.sg/apis/docs/authentication/token",
    "th": "https://developer.webull.co.th/apis/docs/authentication/token",
    "uk": "https://developer.webull-uk.com/apis/docs/authentication/token",
    "us": "https://developer.webull.com/apis/docs/authentication/token",
}


def _2fa_guide_link(region_id: str) -> str:
    """Return the 2FA guide URL for the given region, defaulting to US."""
    return _2FA_GUIDE_LINKS.get(region_id, _2FA_GUIDE_LINKS["us"])


def _supports_unicode() -> bool:
    """Return True if stdout/stderr can safely render Unicode box-drawing characters.

    On Windows with non-UTF-8 codepages (e.g. cp932, cp1252) Unicode
    box-drawing characters render as garbled text, so we fall back to ASCII.
    """
    encoding = getattr(sys.stdout, "encoding", None) or ""
    return encoding.lower().replace("-", "") in ("utf8", "utf16", "utf32")


class TwoFactorAuthRequiredError(Exception):
    """Raised when 2FA verification is required but user hasn't approved yet."""

    def __init__(self, region_id: str, environment: str) -> None:
        self.region_id = region_id
        self.environment = environment
        guide_link = _2fa_guide_link(region_id)
        if _supports_unicode():
            guide_box = (
                "╔══════════════════════════════════════════════════════════╗\n"
                "║  2FA Setup Guide:                                       ║\n"
                f"║  {guide_link:<55s}║\n"
                "╚══════════════════════════════════════════════════════════╝\n"
            )
        else:
            guide_box = (
                "+----------------------------------------------------------+\n"
                "|  2FA Setup Guide:                                        |\n"
                f"|  {guide_link:<56s}|\n"
                "+----------------------------------------------------------+\n"
            )
        message = (
            "2FA Authentication Required\n"
            "===========================\n"
            "\n"
            "Your account requires Two-Factor Authentication (2FA).\n"
            "The MCP server cannot wait for 2FA approval in stdio mode.\n"
            "\n"
            "Steps to resolve:\n"
            "\n"
            "  1. Run:  webull-openapi-mcp auth\n"
            "  2. Approve the 2FA request in your Webull app\n"
            "  3. Restart the MCP server\n"
            "\n"
            f"{guide_box}"
            "\n"
            f"Region: {region_id.upper()}  |  Environment: {environment.upper()}\n"
        )
        super().__init__(message)


class DeviceNotRegisteredError(Exception):
    """Raised when no device is registered for 2FA verification."""

    def __init__(self, region_id: str, environment: str) -> None:
        self.region_id = region_id
        self.environment = environment
        guide_link = _2fa_guide_link(region_id)
        if _supports_unicode():
            guide_box = (
                "╔══════════════════════════════════════════════════════════╗\n"
                "║  2FA Setup Guide:                                       ║\n"
                f"║  {guide_link:<55s}║\n"
                "╚══════════════════════════════════════════════════════════╝\n"
            )
        else:
            guide_box = (
                "+----------------------------------------------------------+\n"
                "|  2FA Setup Guide:                                        |\n"
                f"|  {guide_link:<56s}|\n"
                "+----------------------------------------------------------+\n"
            )
        message = (
            "Device Not Registered\n"
            "=====================\n"
            "\n"
            "No device is registered for 2FA verification with your Webull account.\n"
            "\n"
            "Steps to resolve:\n"
            "\n"
            "  1. Download the latest Webull mobile app\n"
            "  2. Log in with the account associated with your API credentials\n"
            "  3. Complete the device registration/verification process\n"
            "  4. Run:  webull-openapi-mcp auth\n"
            "\n"
            f"{guide_box}"
            "\n"
            f"Region: {region_id.upper()}  |  Environment: {environment.upper()}\n"
        )
        super().__init__(message)

# UAT endpoint configuration.
#
# The SDK's built-in endpoints.json only contains production endpoints.
# For UAT, we must register all three endpoint types via add_endpoint():
#   - api (DEFAULT): Used by TradeClient for trading operations
#   - quotes-api (QUOTES): Used by DataClient.quotes_client for market data
#   - events-api (EVENTS): Used by TradeEventsClient for streaming events
#
# For production, the SDK automatically resolves endpoints from endpoints.json
# based on each request's api_type - no add_endpoint() calls needed.
UAT_ENDPOINTS: dict = {
    "default_region": "us",
    "regions": ["us", "hk", "jp", "sg", "th", "my", "uk", "mx", "br"],
    "region_mapping": {
        "us": {
            "api": "us-openapi-alb.uat.webullbroker.com",
            "quotes-api": "us-openapi-quotes-api.uat.webullbroker.com",
            "events-api": "us-openapi-events.uat.webullbroker.com",
        },
        "hk": {
            "api": "api.sandbox.webull.hk",
            "quotes-api": "data-api.sandbox.webull.hk",
            "events-api": "events-api.sandbox.webull.hk",
        },
        "jp": {
            "api": "jp-openapi-alb.uat.webullbroker.com",
            "quotes-api": "data-api.uat.webullbroker.com",
            "events-api": "jp-openapi-events.uat.webullbroker.com",
        },
        "sg": {
            "api": "sg-api.uat.webullbroker.com",
            "quotes-api": "data-api.uat.webullbroker.com",
            "events-api": "sg-events-api.uat.webullbroker.com",
        },
        "th": {
            "api": "th-api.uat.webullbroker.com",
            "quotes-api": "data-api.uat.webullbroker.com",
            "events-api": "th-events-api.uat.webullbroker.com",
        },
        "my": {
            "api": "my-api.uat.webullbroker.com",
            "quotes-api": "data-api.uat.webullbroker.com",
            "events-api": "my-events-api.uat.webullbroker.com",
        },
        "uk": {
            "api": "uk-api.uat.webullbroker.com",
            "quotes-api": "data-api.uat.webullbroker.com",
            "events-api": "uk-events-api.uat.webullbroker.com",
        },
        "mx": {
            "api": "us-openapi-alb.uat.webullbroker.com",
            "quotes-api": "us-openapi-quotes-api.uat.webullbroker.com",
            "events-api": "us-openapi-events.uat.webullbroker.com",
        },
        "br": {
            "api": "us-openapi-alb.uat.webullbroker.com",
            "quotes-api": "us-openapi-quotes-api.uat.webullbroker.com",
            "events-api": "us-openapi-events.uat.webullbroker.com",
        },
    },
}

# Mapping from our config keys to SDK api_type constants
_API_TYPE_MAP = {
    "api": DEFAULT,
    "quotes-api": QUOTES,
    "events-api": EVENTS,
}


def _configure_uat_endpoints(api_client: ApiClient, cfg: ServerConfig) -> None:
    """Inject UAT endpoints when running in UAT environment."""
    if cfg.environment != "uat":
        return
    region_id = cfg.region_id.lower()
    region_cfg = UAT_ENDPOINTS["region_mapping"].get(region_id)
    if not region_cfg:
        return
    for key, api_type in _API_TYPE_MAP.items():
        endpoint = region_cfg.get(key)
        if endpoint:
            api_client.add_endpoint(region_id, endpoint, api_type)


def _configure_logging(api_client: ApiClient) -> None:
    """Redirect SDK logging to stderr with configurable level."""
    log_level_str = os.environ.get("WEBULL_LOG_LEVEL", "WARNING").upper()
    log_level = getattr(logging, log_level_str, logging.WARNING)
    api_client.set_stream_logger(log_level=log_level, stream=sys.stderr)


def _create_clients(
    api_client: ApiClient, cfg: ServerConfig,
) -> tuple[TradeClient, DataClient]:
    """Create TradeClient and DataClient, translating auth errors."""
    try:
        trade = TradeClient(api_client)
        data = DataClient(api_client)
    except ServerException as e:
        if e.error_code == "NO_AVAILABLE_DEVICE":
            raise DeviceNotRegisteredError(cfg.region_id, cfg.environment) from e
        raise
    except ClientException as e:
        if "ERROR_INIT_TOKEN" in str(e) or "ERROR_CHECK_TOKEN" in str(e):
            raise TwoFactorAuthRequiredError(cfg.region_id, cfg.environment) from e
        raise
    return trade, data


class WebullSDKClient:
    """Manage ApiClient / TradeClient / DataClient lifecycle.

    This is the *only* layer that touches the Webull SDK directly.
    Token persistence is handled entirely by the SDK's built-in
    TokenManager / TokenStorage — we just forward ``token_dir`` via
    ``api_client.set_token_dir()``.
    """

    # Short timeout for MCP server mode - fail fast if 2FA required
    # Users should run 'auth' command first for interactive 2FA
    MCP_TOKEN_CHECK_DURATION = 10  # seconds (vs SDK default 300)
    MCP_TOKEN_CHECK_INTERVAL = 2   # seconds (vs SDK default 5)

    def __init__(self, config: ServerConfig) -> None:
        self._config = config
        self._api_client: ApiClient | None = None
        self._trade_client: TradeClient | None = None
        self._data_client: DataClient | None = None

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def initialize(self, interactive: bool = False) -> None:
        """Create and wire up all SDK clients.

        Args:
            interactive: If True, use longer timeout for interactive auth.
                        If False (default), use short timeout for MCP server.

        Steps:
        1. Create ``ApiClient(app_key, app_secret, region_id)``
        2. If ``token_dir`` is configured, forward it to the SDK
        3. For UAT environments, inject all UAT endpoints (api, quotes-api, events-api)
        4. Configure SDK logging level
        5. Create ``TradeClient`` (triggers automatic Token init)
        6. Create ``DataClient`` (triggers automatic Token init)
        """
        cfg = self._config
        region_id = cfg.region_id.lower()

        # Set client source identifier so SDK can distinguish MCP calls from native SDK calls
        os.environ.setdefault("WEBULL_CLIENT_SOURCE", "mcp")

        # Determine token check timeout based on mode
        if interactive:
            token_check_duration = 300
            token_check_interval = 5
        else:
            token_check_duration = self.MCP_TOKEN_CHECK_DURATION
            token_check_interval = self.MCP_TOKEN_CHECK_INTERVAL

        # 1. Core API client with custom token check timeout
        api_client = ApiClient(
            cfg.app_key,
            cfg.app_secret,
            region_id,
            token_check_duration_seconds=token_check_duration,
            token_check_interval_seconds=token_check_interval,
        )

        # 2. Token persistence directory
        if cfg.token_dir:
            api_client.set_token_dir(cfg.token_dir)

        # 3. UAT endpoint injection
        _configure_uat_endpoints(api_client, cfg)

        # 4. SDK logging configuration
        _configure_logging(api_client)

        # 5 & 6. Trade / Data clients
        self._api_client = api_client
        self._trade_client, self._data_client = _create_clients(api_client, cfg)

    # ------------------------------------------------------------------
    # Property accessors
    # ------------------------------------------------------------------

    @property
    def trade(self) -> TradeClient:
        """Return the initialised TradeClient."""
        if self._trade_client is None:
            raise RuntimeError("SDK not initialised — call initialize() first")
        return self._trade_client

    @property
    def data(self) -> DataClient:
        """Return the initialised DataClient."""
        if self._data_client is None:
            raise RuntimeError("SDK not initialised — call initialize() first")
        return self._data_client
