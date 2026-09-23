"""Order validation for Webull MCP Server.

Provides unified order validation including:
- Basic parameter validation (side, quantity, price fields)
- Region-specific validation (order types, time-in-force, trading sessions)
- Feature availability checks (combo orders, option strategies, algo orders)
- BCAN validation for HK orders
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re
from typing import TYPE_CHECKING

from webull_openapi_mcp.constants import (
    STRATEGY_LEG_COUNT,
    VALID_ACCOUNT_TAX_TYPES,
    VALID_ENTRUST_TYPES,
    VALID_MARGIN_TYPES,
    VALID_OPTION_ORDER_TYPES,
    VALID_OPTION_TIF,
    VALID_OPTION_TYPES,
    VALID_POSITION_INTENTS,
    VALID_SIDES,
)
from webull_openapi_mcp.errors import (
    FeatureNotSupportedError,
    RegionValidationError,
    ValidationError,
)


# ---------------------------------------------------------------------------
# Client Order ID validation
# ---------------------------------------------------------------------------

_MAX_CLIENT_ORDER_ID_LEN = 32
_MAX_PAGINATION_KEY_LEN = 2048
_CLIENT_ORDER_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def validate_client_order_id(client_order_id: str | None) -> None:
    """Validate a public client order ID when one is provided."""
    if client_order_id is None:
        return
    if not client_order_id:
        raise ValidationError("client_order_id must not be empty", field="client_order_id")
    if len(client_order_id) > _MAX_CLIENT_ORDER_ID_LEN:
        raise ValidationError(
            f"client_order_id exceeds max length of {_MAX_CLIENT_ORDER_ID_LEN} characters "
            f"(got {len(client_order_id)})",
            field="client_order_id",
        )
    if not _CLIENT_ORDER_ID_PATTERN.fullmatch(client_order_id):
        raise ValidationError(
            "client_order_id may contain only letters, numbers, underscores, and hyphens",
            field="client_order_id",
        )


def validate_pagination_key(pagination_key: str | None) -> None:
    """Validate an opaque pagination cursor without interpreting it."""
    if pagination_key is None:
        return
    if not isinstance(pagination_key, str) or not pagination_key:
        raise ValidationError("pagination_key must not be empty", field="pagination_key")
    if len(pagination_key) > _MAX_PAGINATION_KEY_LEN:
        raise ValidationError(
            f"pagination_key exceeds max length of {_MAX_PAGINATION_KEY_LEN} characters",
            field="pagination_key",
        )


def validate_enum(value: str | None, valid_values: frozenset[str], field: str) -> None:
    """Validate an optional enum value against an explicit allowlist."""
    if value is not None and value not in valid_values:
        raise ValidationError(
            f"Invalid {field}, must be one of {sorted(valid_values)}",
            field=field,
        )


def validate_positive_decimal(value: object, field: str) -> None:
    """Validate a finite decimal value greater than zero."""
    if isinstance(value, bool):
        raise ValidationError(f"{field} must be a positive decimal", field=field)
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(f"{field} must be a positive decimal", field=field)
    if not decimal_value.is_finite() or decimal_value <= 0:
        raise ValidationError(f"{field} must be a positive decimal", field=field)


def validate_positive_whole_number(value: object, field: str, maximum: int | None = None) -> None:
    """Validate a positive whole number with an optional upper bound.

    Only genuine integers (or integer-valued strings) are accepted. Booleans are
    rejected because bool is a subclass of int in Python, and floats are rejected
    even when integer-valued (e.g. 1.0) to avoid silently coercing non-integer
    inputs into a quantity.
    """
    if isinstance(value, bool) or isinstance(value, float):
        raise ValidationError(f"{field} must be a positive whole number", field=field)
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(f"{field} must be a positive whole number", field=field)
    if not decimal_value.is_finite() or decimal_value <= 0 or decimal_value != decimal_value.to_integral_value():
        raise ValidationError(f"{field} must be a positive whole number", field=field)
    if maximum is not None and decimal_value > maximum:
        raise ValidationError(f"{field} must be between 1 and {maximum}", field=field)


def validate_symbol_list(symbols: str, field: str = "symbols", maximum: int = 20) -> list[str]:
    """Validate and split a comma-separated symbol list."""
    if not isinstance(symbols, str):
        raise ValidationError(f"{field} must be a comma-separated string", field=field)
    values = [symbol.strip() for symbol in symbols.split(",") if symbol.strip()]
    if not values:
        raise ValidationError(f"{field} must include at least one symbol", field=field)
    if len(values) > maximum:
        raise ValidationError(f"{field} supports at most {maximum} symbols", field=field)
    return values


def validate_iso_date(value: str | None, field: str) -> None:
    """Validate an optional ISO calendar date."""
    if value is None:
        return
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must use YYYY-MM-DD format", field=field)


def _parse_iso_utc_time(value: str, field: str) -> datetime:
    if not isinstance(value, str) or "T" not in value or not value.endswith("Z"):
        raise ValidationError(f"{field} must be an ISO 8601 UTC timestamp ending in Z", field=field)
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        raise ValidationError(f"{field} must be a valid ISO 8601 UTC timestamp", field=field)
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValidationError(f"{field} must be in UTC", field=field)
    return parsed


def validate_iso_utc_range(start_time: str | None, end_time: str | None) -> None:
    """Validate optional UTC timestamps and their chronological order."""
    start = _parse_iso_utc_time(start_time, "start_time") if start_time is not None else None
    end = _parse_iso_utc_time(end_time, "end_time") if end_time is not None else None
    if start is not None and end is not None and start > end:
        raise ValidationError("start_time must not be later than end_time", field="start_time")


def normalize_iso_utc_millis(value: str | None) -> str | None:
    """Normalize a second-precision ISO 8601 UTC timestamp to millisecond form.

    The backend requires millisecond precision (e.g. 2026-10-01T00:00:00.000Z) and
    rejects second-precision input (e.g. 2026-10-01T00:00:00Z). Callers stay lenient
    and accept both forms; this helper upgrades a second-precision value to
    millisecond form before the request is sent while preserving the Z/UTC marker.
    A value that already carries a fractional-seconds component is returned
    unchanged, so milliseconds are never double-appended.

    Returns None when value is None. Values that are not second-precision
    ...SSZ timestamps are returned unchanged; validation is expected to have run
    separately (see validate_iso_utc_range).
    """
    if value is None:
        return value
    if not isinstance(value, str) or not value.endswith("Z") or "." in value:
        return value
    return value[:-1] + ".000Z"


def validate_close_contracts(close_contracts: object) -> None:
    """Validate JP close_contracts payload."""
    if close_contracts is None:
        return
    if not isinstance(close_contracts, list):
        raise ValidationError("close_contracts must be a list", field="close_contracts")
    if len(close_contracts) > 10:
        raise ValidationError("close_contracts supports at most 10 contracts", field="close_contracts")
    for i, contract in enumerate(close_contracts):
        if not isinstance(contract, dict):
            raise ValidationError(
                f"close_contracts[{i}] must be an object with contract_id and quantity",
                field="close_contracts",
            )
        if not contract.get("contract_id"):
            raise ValidationError(
                f"close_contracts[{i}].contract_id is required",
                field="close_contracts",
            )
        quantity = contract.get("quantity")
        if quantity is None:
            raise ValidationError(
                f"close_contracts[{i}].quantity is required",
                field="close_contracts",
            )
        try:
            if float(quantity) <= 0:
                raise ValueError
        except (TypeError, ValueError):
            raise ValidationError(
                f"close_contracts[{i}].quantity must be > 0",
                field="close_contracts",
            )


if TYPE_CHECKING:
    from webull_openapi_mcp.config import ServerConfig
    from webull_openapi_mcp.region_config import RegionConfig


class OrderValidator:
    """Unified order validator with region-specific rules."""

    def __init__(self, region_config: RegionConfig, server_config: ServerConfig) -> None:
        """Initialize the validator.

        Parameters
        ----------
        region_config
            Region-specific configuration with valid enum sets.
        server_config
            Server configuration with order limits.
        """
        self.region_config = region_config
        self.server_config = server_config

    # =========================================================================
    # High-level validation methods
    # =========================================================================

    def validate_stock_order(self, params: dict) -> None:
        """Validate stock order parameters.

        Validates: side, order_type, time_in_force, trading_session, quantity,
        price fields, symbol whitelist, and BCAN for HK region.
        """
        self._validate_side(params.get("side"))
        self._validate_order_market(params.get("market"))
        self._validate_order_type(params.get("order_type"), params.get("market"))
        self._validate_time_in_force(params.get("time_in_force"), params.get("market"))
        self._validate_trading_session(params.get("trading_session"))
        # Skip quantity/notional validation for AMOUNT entrust_type (fractional shares)
        if params.get("entrust_type") != "AMOUNT":
            self._validate_quantity(params.get("quantity"), params.get("limit_price"), params.get("market"))
        self._validate_price_fields(
            params.get("order_type"),
            params.get("limit_price"),
            params.get("stop_price"),
        )
        self._validate_symbol_whitelist(params.get("symbol"))
        self._validate_entrust_type(params.get("entrust_type"))
        
        # HK-specific: BCAN validation
        if self.region_config.region_id == "hk":
            self._validate_bcan(params)

        # JP-specific order fields
        if self.region_config.region_id == "jp":
            self._validate_jp_order_fields(params)

    def validate_combo_order(self, params: dict) -> None:
        """Validate combo order parameters (US only)."""
        self._validate_combo_type(params.get("combo_type"))
        
        # Validate each order leg
        orders = params.get("orders", [])
        for order in orders:
            self._validate_side(order.get("side"))
            self._validate_order_type(order.get("order_type"), order.get("market"))
            if order.get("time_in_force"):
                self._validate_time_in_force(order.get("time_in_force"))

    def validate_option_order(self, params: dict) -> None:
        """Validate a single-leg US-listed option order."""
        side = params.get("side")
        if side not in {"BUY", "SELL"}:
            raise ValidationError("side must be BUY or SELL for option orders", field="side")
        self._validate_option_order_type(params.get("order_type"))
        self._validate_option_tif(params.get("time_in_force"))
        self._validate_option_price_fields(
            params.get("order_type"),
            params.get("limit_price"),
            params.get("stop_price"),
        )
        if "quantity" in params:
            max_quantity = self.server_config.max_order_quantity
            validate_positive_whole_number(
                params.get("quantity"),
                "quantity",
                maximum=int(max_quantity) if max_quantity is not None else None,
            )
        if "strike_price" in params:
            validate_positive_decimal(params.get("strike_price"), "strike_price")
        validate_enum(params.get("option_type"), VALID_OPTION_TYPES, "option_type")
        validate_enum(params.get("position_intent"), VALID_POSITION_INTENTS, "position_intent")
        validate_iso_date(params.get("expiration_date"), "expiration_date")
        if "symbol" in params:
            symbol = params.get("symbol")
            if not isinstance(symbol, str) or not symbol.strip():
                raise ValidationError("symbol must not be empty", field="symbol")
            self._validate_symbol_whitelist(symbol)
        # JP requires account_tax_type on option orders (same as stock orders).
        if self.region_config.region_id == "jp":
            account_tax_type = params.get("account_tax_type")
            if account_tax_type is None:
                raise ValidationError(
                    "account_tax_type is required for JP option orders", field="account_tax_type"
                )
            if account_tax_type not in VALID_ACCOUNT_TAX_TYPES:
                raise ValidationError(
                    "Invalid account_tax_type, "
                    f"must be one of {sorted(VALID_ACCOUNT_TAX_TYPES)}",
                    field="account_tax_type",
                )
            if params.get("position_intent") is None:
                raise ValidationError(
                    "position_intent is required for JP option orders",
                    field="position_intent",
                )

    def validate_option_strategy_order(self, params: dict) -> None:
        """Validate option strategy order parameters (US only)."""
        strategy = params.get("strategy")
        self._validate_option_strategy(strategy)
        
        # Validate leg count
        legs = params.get("legs", [])
        self._validate_strategy_leg_count(strategy, len(legs))
        
        # Validate each leg
        for i, leg in enumerate(legs):
            self._validate_option_leg(leg, i)
        
        # Validate order parameters
        self._validate_option_order_type(params.get("order_type"))
        self._validate_option_tif(params.get("time_in_force"))

    def validate_algo_order(self, params: dict) -> None:
        """Validate algorithmic order parameters (US only)."""
        if not self.region_config.supports_algo_orders:
            raise FeatureNotSupportedError(
                feature="algo_orders",
                region_id=self.region_config.region_id,
            )
        
        self._validate_side(params.get("side"))
        self._validate_quantity(params.get("quantity"), params.get("limit_price"))
        
        algo_type = params.get("algo_type")
        if algo_type is None:
            raise ValidationError("algo_type is required", field="algo_type")
        
        valid_algo_types = {"TWAP", "VWAP", "POV"}
        if algo_type not in valid_algo_types:
            raise ValidationError(
                f"Invalid algo_type. Valid values: {', '.join(sorted(valid_algo_types))}",
                field="algo_type",
            )
        
        # POV requires target_vol_percent
        if algo_type == "POV" and params.get("target_vol_percent") is None:
            raise ValidationError(
                "target_vol_percent is required for POV algorithm",
                field="target_vol_percent",
            )

    # =========================================================================
    # Basic validation methods
    # =========================================================================

    def _validate_side(self, side: str | None) -> None:
        """Validate trade side."""
        if side not in VALID_SIDES:
            raise ValidationError(
                f"Invalid side, must be one of {sorted(VALID_SIDES)}",
                field="side",
            )

    def _validate_quantity(self, quantity: float | None, price: float | None, market: str | None = None) -> None:
        """Validate quantity and notional value.
        
        Notional limits are market-specific:
        - US market: USD limit
        - HK market: HKD limit
        - CN market: CNH limit
        """
        if quantity is None or quantity <= 0:
            raise ValidationError(
                "quantity must be > 0",
                field="quantity",
            )
        if quantity > self.server_config.max_order_quantity:
            raise ValidationError(
                f"quantity exceeds max_order_quantity {self.server_config.max_order_quantity}",
                field="quantity",
            )
        
        # Notional value check with market-specific limits
        if price is not None:
            notional = quantity * price
            max_notional, currency = self.server_config.get_max_notional_for_market(market)
            
            if notional > max_notional:
                raise ValidationError(
                    f"Notional value exceeds max_order_notional_{currency.lower()} "
                    f"{max_notional:.2f} {currency}",
                    field="notional",
                )

    def _validate_price_fields(
        self, order_type: str | None, limit_price: float | None, stop_price: float | None
    ) -> None:
        """Validate price fields based on order type."""
        if order_type == "LIMIT" and limit_price is None:
            raise ValidationError("LIMIT order requires 'limit_price' field", field="limit_price")
        
        if order_type == "STOP_LOSS" and stop_price is None:
            raise ValidationError("STOP_LOSS order requires 'stop_price' field", field="stop_price")
        
        if order_type == "STOP_LOSS_LIMIT":
            if limit_price is None:
                raise ValidationError("STOP_LOSS_LIMIT order requires 'limit_price' field", field="limit_price")
            if stop_price is None:
                raise ValidationError("STOP_LOSS_LIMIT order requires 'stop_price' field", field="stop_price")

    def _validate_symbol_whitelist(self, symbol: str | None) -> None:
        """Validate symbol against whitelist if configured."""
        if self.server_config.symbol_whitelist is not None and symbol not in self.server_config.symbol_whitelist:
            raise ValidationError(
                "symbol is not in the allowed whitelist",
                field="symbol",
            )

    def _validate_entrust_type(self, entrust_type: str | None) -> None:
        """Validate entrust type if provided."""
        if entrust_type is None:
            return  # Optional, defaults to QTY in order tools
        if entrust_type not in VALID_ENTRUST_TYPES:
            raise ValidationError(
                f"Invalid entrust_type, must be one of {sorted(VALID_ENTRUST_TYPES)}",
                field="entrust_type",
            )

    # =========================================================================
    # Region-specific validation methods
    # =========================================================================

    def _validate_order_market(self, market: str | None) -> None:
        """Validate order market against region-specific market support."""
        if market is None:
            return
        market = market.upper()
        if market not in self.region_config.valid_order_markets:
            raise RegionValidationError(
                param_name="market",
                value=market,
                region_id=self.region_config.region_id,
                valid_values=self.region_config.valid_order_markets,
            )

    def _validate_order_type(self, order_type: str | None, market: str | None = None) -> None:
        """Validate order type against region-specific valid values."""
        if order_type is None:
            raise ValidationError("order_type is required", field="order_type")

        if self.region_config.region_id == "jp" and market:
            market_order_types: dict[str, frozenset[str]] = {
                "JP": frozenset({"LIMIT", "MARKET"}),
                "US": frozenset({"LIMIT", "MARKET", "STOP_LOSS", "STOP_LOSS_LIMIT"}),
            }
            valid = market_order_types.get(market.upper())
            if valid and order_type not in valid:
                raise ValidationError(
                    f"Invalid order_type for {market} market. "
                    f"Valid values: {', '.join(sorted(valid))}",
                    field="order_type",
                )
            if valid:
                return

        if order_type not in self.region_config.valid_order_types:
            raise RegionValidationError(
                param_name="order_type",
                value=order_type,
                region_id=self.region_config.region_id,
                valid_values=self.region_config.valid_order_types,
            )

    def _validate_time_in_force(self, tif: str | None, market: str | None = None) -> None:
        """Validate time-in-force against region and market-specific rules.
        
        HK region market-specific rules:
        - US market: DAY, GTC, GTD
        - HK market: DAY, GTC
        - CN market: DAY only
        """
        if tif is None:
            raise ValidationError("time_in_force is required", field="time_in_force")
        
        # Market-specific TIF validation for HK region
        if self.region_config.region_id == "hk" and market:
            market_tif: dict[str, frozenset[str]] = {
                "CN": frozenset({"DAY"}),
                "HK": frozenset({"DAY", "GTC"}),
                "US": frozenset({"DAY", "GTC", "GTD"}),
            }
            valid = market_tif.get(market.upper())
            if valid and tif not in valid:
                raise ValidationError(
                    f"Invalid time_in_force for {market} market. "
                    f"Valid values: {', '.join(sorted(valid))}",
                    field="time_in_force",
                )
            return

        # Market-specific TIF validation for JP region
        if self.region_config.region_id == "jp" and market:
            market_tif: dict[str, frozenset[str]] = {
                "JP": frozenset({"DAY"}),
                "US": frozenset({"DAY", "GTC", "GTD"}),
            }
            valid = market_tif.get(market.upper())
            if valid and tif not in valid:
                raise ValidationError(
                    f"Invalid time_in_force for {market} market. "
                    f"Valid values: {', '.join(sorted(valid))}",
                    field="time_in_force",
                )
            if valid:
                return

        if tif not in self.region_config.valid_time_in_force:
            raise RegionValidationError(
                param_name="time_in_force",
                value=tif,
                region_id=self.region_config.region_id,
                valid_values=self.region_config.valid_time_in_force,
            )

    def _validate_trading_session(self, session: str | None) -> None:
        """Validate trading session against region-specific valid values."""
        if session is None:
            return  # Trading session is optional
        
        if session not in self.region_config.valid_trading_sessions:
            raise RegionValidationError(
                param_name="trading_session",
                value=session,
                region_id=self.region_config.region_id,
                valid_values=self.region_config.valid_trading_sessions,
            )

    def _validate_combo_type(self, combo_type: str | None) -> None:
        """Validate combo type (US only)."""
        if not self.region_config.supports_combo_orders:
            raise FeatureNotSupportedError(
                feature="combo_orders",
                region_id=self.region_config.region_id,
            )
        
        if combo_type is None:
            raise ValidationError("combo_type is required", field="combo_type")
        
        if combo_type not in self.region_config.valid_combo_types:
            raise RegionValidationError(
                param_name="combo_type",
                value=combo_type,
                region_id=self.region_config.region_id,
                valid_values=self.region_config.valid_combo_types,
            )

    def _validate_market_category(self, category: str | None) -> None:
        """Validate market category against region-specific valid values."""
        if category is None:
            return
        
        if category not in self.region_config.valid_market_categories:
            raise RegionValidationError(
                param_name="market_category",
                value=category,
                region_id=self.region_config.region_id,
                valid_values=self.region_config.valid_market_categories,
            )

    def _validate_bcan(self, params: dict) -> None:
        """Validate BCAN (no_party_ids) for HK orders."""
        no_party_ids = params.get("no_party_ids")
        if no_party_ids is None:
            return  # BCAN is optional
        
        if not isinstance(no_party_ids, list):
            raise ValidationError(
                "no_party_ids must be a list of BCAN objects",
                field="no_party_ids",
            )
        
        for i, party in enumerate(no_party_ids):
            if not isinstance(party, dict):
                raise ValidationError(
                    f"no_party_ids[{i}] must be an object with party_id and party_id_source",
                    field="no_party_ids",
                )
            if "party_id" not in party:
                raise ValidationError(
                    f"no_party_ids[{i}].party_id is required",
                    field="no_party_ids",
                )
            if "party_id_source" not in party:
                raise ValidationError(
                    f"no_party_ids[{i}].party_id_source is required",
                    field="no_party_ids",
                )

    def _validate_jp_order_fields(self, params: dict) -> None:
        """Validate JP-specific order fields."""
        account_tax_type = params.get("account_tax_type")
        if account_tax_type is None:
            raise ValidationError("account_tax_type is required for JP orders", field="account_tax_type")
        if account_tax_type not in VALID_ACCOUNT_TAX_TYPES:
            raise ValidationError(
                "Invalid account_tax_type, "
                f"must be one of {sorted(VALID_ACCOUNT_TAX_TYPES)}",
                field="account_tax_type",
            )

        margin_type = params.get("margin_type")
        if margin_type is not None and margin_type not in VALID_MARGIN_TYPES:
            raise ValidationError(
                f"Invalid margin_type, must be one of {sorted(VALID_MARGIN_TYPES)}",
                field="margin_type",
            )

        validate_close_contracts(params.get("close_contracts"))

    # =========================================================================
    # Option-specific validation methods
    # =========================================================================

    def _validate_option_order_type(self, order_type: str | None) -> None:
        """Validate option order type."""
        if order_type not in VALID_OPTION_ORDER_TYPES:
            raise ValidationError(
                f"Invalid option order_type, must be one of {sorted(VALID_OPTION_ORDER_TYPES)}",
                field="order_type",
            )

    def _validate_option_tif(self, tif: str | None) -> None:
        """Validate option time-in-force."""
        if tif not in VALID_OPTION_TIF:
            raise ValidationError(
                f"Invalid option time_in_force, must be one of {sorted(VALID_OPTION_TIF)}",
                field="time_in_force",
            )

    def _validate_option_price_fields(
        self, order_type: str | None, limit_price: float | None, stop_price: float | None
    ) -> None:
        """Validate required option prices and reject non-positive values."""
        if order_type in ("LIMIT", "STOP_LOSS_LIMIT") and limit_price is None:
            raise ValidationError(f"{order_type} option order requires 'limit_price' field", field="limit_price")
        if order_type in ("STOP_LOSS", "STOP_LOSS_LIMIT") and stop_price is None:
            raise ValidationError(f"{order_type} option order requires 'stop_price' field", field="stop_price")
        if limit_price is not None:
            validate_positive_decimal(limit_price, "limit_price")
        if stop_price is not None:
            validate_positive_decimal(stop_price, "stop_price")

    def _validate_option_strategy(self, strategy: str | None) -> None:
        """Validate option strategy (US only for multi-leg)."""
        if strategy == "SINGLE":
            return  # SINGLE is always allowed
        
        if not self.region_config.supports_option_strategies:
            raise FeatureNotSupportedError(
                feature="option_strategies",
                region_id=self.region_config.region_id,
            )
        
        if strategy is None:
            raise ValidationError("strategy is required", field="strategy")
        
        if strategy not in self.region_config.valid_option_strategies:
            raise RegionValidationError(
                param_name="strategy",
                value=strategy,
                region_id=self.region_config.region_id,
                valid_values=self.region_config.valid_option_strategies,
            )

    def _validate_strategy_leg_count(self, strategy: str | None, leg_count: int) -> None:
        """Validate that leg count matches strategy requirements."""
        if strategy is None:
            return
        
        leg_range = STRATEGY_LEG_COUNT.get(strategy)
        if leg_range is None:
            return  # Unknown strategy, skip leg validation
        
        min_legs, max_legs = leg_range
        if leg_count < min_legs or leg_count > max_legs:
            if min_legs == max_legs:
                raise ValidationError(
                    f"strategy requires exactly {min_legs} leg(s)",
                    field="legs",
                )
            else:
                raise ValidationError(
                    f"strategy requires {min_legs}-{max_legs} legs",
                    field="legs",
                )

    _REQUIRED_LEG_FIELDS = frozenset({
        "symbol", "side", "quantity", "option_type", "strike_price", "option_expire_date",
    })

    def _validate_option_leg(self, leg: dict, index: int) -> None:
        """Validate a single option leg. Skip validation for EQUITY legs (e.g. COVERED_STOCK)."""
        if leg.get("instrument_type") == "EQUITY":
            return  # Equity legs only need symbol, side, quantity — no option fields
        missing = self._REQUIRED_LEG_FIELDS - set(leg.keys())
        if missing:
            raise ValidationError(
                f"Leg {index} missing required fields: {sorted(missing)}",
                field="legs",
            )


# =============================================================================
# Legacy functions for backward compatibility
# =============================================================================

def validate_order(params: dict, config: ServerConfig) -> None:
    """Validate stock/crypto/futures order parameters (legacy function).

    This function is kept for backward compatibility.
    New code should use OrderValidator class.
    """
    from webull_openapi_mcp.region_config import get_region_config
    
    region_config = get_region_config(config.region_id)
    validator = OrderValidator(region_config, config)
    validator.validate_stock_order(params)


def validate_equity_order(params: dict, config: ServerConfig) -> None:
    """Validate equity (stock) order parameters (legacy function).

    This function is kept for backward compatibility.
    New code should use OrderValidator class.
    """
    from webull_openapi_mcp.region_config import get_region_config
    
    region_config = get_region_config(config.region_id)
    validator = OrderValidator(region_config, config)
    validator.validate_stock_order(params)


# Alias for consistency
validate_stock_order = validate_equity_order


def validate_option_order(params: dict, config: ServerConfig) -> None:
    """Validate option order parameters (legacy function).

    This function is kept for backward compatibility.
    New code should use OrderValidator class.
    """
    from webull_openapi_mcp.region_config import get_region_config
    
    region_config = get_region_config(config.region_id)
    validator = OrderValidator(region_config, config)
    
    strategy = params.get("strategy")
    if strategy and strategy != "SINGLE":
        validator.validate_option_strategy_order(params)
    else:
        validator.validate_option_order(params)


def validate_combo_order(params: dict, config: ServerConfig) -> None:
    """Validate combo order parameters."""
    from webull_openapi_mcp.region_config import get_region_config

    region_config = get_region_config(config.region_id)
    validator = OrderValidator(region_config, config)
    validator.validate_combo_order(params)


def validate_algo_order(params: dict, config: ServerConfig) -> None:
    """Validate algorithmic order parameters."""
    from webull_openapi_mcp.region_config import get_region_config

    region_config = get_region_config(config.region_id)
    validator = OrderValidator(region_config, config)
    validator.validate_algo_order(params)


def validate_option_strategy_order(params: dict, config: ServerConfig) -> None:
    """Validate multi-leg option strategy order parameters."""
    from webull_openapi_mcp.region_config import get_region_config

    region_config = get_region_config(config.region_id)
    validator = OrderValidator(region_config, config)
    validator.validate_option_strategy_order(params)
