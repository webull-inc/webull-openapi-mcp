"""Exception definitions and SDK error handling for Webull MCP Server."""

from __future__ import annotations


class ConfigError(Exception):
    """Configuration error (missing credentials, invalid values, etc.)."""
    pass


class AuthenticationError(Exception):
    """Authentication-related errors (token, 2FA, etc.)."""
    pass


class ValidationError(Exception):
    """Order local validation failure."""

    def __init__(self, message: str, field: str | None = None):
        self.message = message
        self.field = field
        super().__init__(message)


# =============================================================================
# Region-Specific Errors
# =============================================================================

class RegionError(Exception):
    """Base class for region-related errors."""
    pass


class UnsupportedRegionError(RegionError):
    """Raised when an unsupported region is configured."""

    def __init__(self, region_id: str, supported: list[str] | None = None) -> None:
        self.region_id = region_id
        self.supported = supported or ["us", "hk"]
        super().__init__(
            f"Unsupported region '{region_id}'. "
            f"Supported regions: {', '.join(sorted(self.supported))}"
        )


class RegionValidationError(ValidationError):
    """Raised when a parameter is invalid for the configured region."""

    def __init__(
        self,
        param_name: str,
        value: str,
        region_id: str,
        valid_values: set[str] | frozenset[str],
    ) -> None:
        self.param_name = param_name
        self.value = value
        self.region_id = region_id
        self.valid_values = valid_values
        message = (
            f"Invalid {param_name} '{value}' for region '{region_id}'. "
            f"Valid values: {', '.join(sorted(valid_values))}"
        )
        super().__init__(message, field=param_name)


class FeatureNotSupportedError(RegionError):
    """Raised when a feature is not supported in the configured region."""

    def __init__(self, feature: str, region_id: str) -> None:
        self.feature = feature
        self.region_id = region_id
        super().__init__(
            f"Feature '{feature}' is not supported in region '{region_id}'"
        )


# Market data tools that need subscription special handling
MARKET_DATA_TOOLS = frozenset({
    "get_stock_snapshot",
    "get_stock_quotes",
    "get_stock_bars",
    "get_stock_bars_single",
    "get_stock_tick",
    "get_stock_footprint",
    "get_futures_tick",
    "get_futures_snapshot",
    "get_futures_depth",
    "get_futures_bars",
    "get_futures_footprint",
    "get_crypto_snapshot",
    "get_crypto_bars",
    "get_event_tick",
    "get_event_snapshot",
    "get_event_depth",
    "get_event_bars",
})

# Region-specific subscription guidance
MARKET_DATA_SUBSCRIPTION_HINTS: dict[str, str] = {
    "br": (
        "Market data requires quotes subscription.\n"
        "Subscribe at: https://www.webull.com.br/quote\n"
        "Guide: https://developer.webull.com.br/apis/docs/market-data-api/subscribe-quotes"
    ),
    "hk": (
        "Market data requires quotes subscription.\n"
        "Subscribe at: https://www.webullapp.hk/quote\n"
        "Guide: https://developer.webull.hk/apis/docs/market-data-api/subscribe-quotes"
    ),
    "jp": (
        "Market data requires quotes subscription.\n"
        "Subscribe at: https://www.webull.co.jp/pricing\n"
        "Guide: https://developer.webull.co.jp/api-doc/market-data/subscribe-quotes/"
    ),
    "mx": (
        "Market data requires quotes subscription.\n"
        "Subscribe at: https://www.webull.com.mx/quote\n"
        "Guide: https://developer.webull.com.mx/apis/docs/market-data-api/subscribe-quotes"
    ),
    "us": (
        "Market data requires quotes subscription.\n"
        "Subscribe at: https://www.webullapp.com/quote\n"
        "Guide: https://developer.webull.com/apis/docs/market-data-api/subscribe-quotes"
    ),
}


def _get_market_data_hint(region_id: str | None = None) -> str:
    """Get market data subscription hint for the given region."""
    if region_id and region_id.lower() in MARKET_DATA_SUBSCRIPTION_HINTS:
        return MARKET_DATA_SUBSCRIPTION_HINTS[region_id.lower()]
    # Fallback: show both
    return (
        "Market data requires quotes subscription.\n\n"
        "HK region:\n"
        "  Subscribe: https://www.webullapp.hk/quote\n"
        "  Guide: https://developer.webull.hk/apis/docs/market-data-api/subscribe-quotes\n\n"
        "US region:\n"
        "  Subscribe: https://www.webullapp.com/quote\n"
        "  Guide: https://developer.webull.com/apis/docs/market-data-api/subscribe-quotes"
        "\n\nJP region:\n"
        "  Subscribe: https://www.webull.co.jp/pricing\n"
        "  Guide: https://developer.webull.co.jp/api-doc/market-data/subscribe-quotes/"
    )


def handle_sdk_exception(e: Exception, tool_name: str, region_id: str | None = None) -> str:
    """Unified SDK exception handler.

    Handles:
    - ServerException: extract http_status + error_code + message,
      with special handling for market data 401/403 and cancel_order 404/403.
    - ClientException: extract parameter error description.
    - Other exceptions: generic error message.
    """
    from webull.core.exception.exceptions import ClientException, ServerException

    if isinstance(e, ServerException):
        http_status = e.http_status

        # Market data 401/403 → subscription hint
        if http_status in (401, 403) and tool_name in MARKET_DATA_TOOLS:
            return _get_market_data_hint(region_id)

        # cancel_order special messages
        if tool_name == "cancel_order":
            if http_status == 404:
                return "Order not found; it may have been filled or already cancelled"
            if http_status == 403:
                return "Permission denied; please check account permissions"

        return f"Server error (HTTP {http_status}): [{e.error_code}] {e.error_msg}"

    if isinstance(e, ClientException):
        return f"Parameter error: [{e.error_code}] {e.error_msg}"

    return f"Internal error: {type(e).__name__}: {e}"
