"""Order validation for Webull MCP Server.

Provides unified order validation including:
- Basic parameter validation (side, quantity, price fields)
- Region-specific validation (order types, time-in-force, trading sessions)
- Feature availability checks (combo orders, option strategies, algo orders)
- BCAN validation for HK orders
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from webull_openapi_mcp.constants import (
    STRATEGY_LEG_COUNT,
    VALID_ACCOUNT_TAX_TYPES,
    VALID_ENTRUST_TYPES,
    VALID_MARGIN_TYPES,
    VALID_OPTION_ORDER_TYPES,
    VALID_OPTION_TIF,
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


def validate_client_order_id(client_order_id: str | None) -> None:
    """Validate client_order_id: max 32 chars, non-empty if provided.

    Raises ValidationError if invalid.
    """
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
        # AMOUNT entrust_type (fractional shares): cap the dollar amount instead of quantity
        if params.get("entrust_type") == "AMOUNT":
            self._validate_cash_amount(params.get("total_cash_amount"), params.get("market"))
        else:
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
        """Validate combo order parameters (US only).

        Applies quantity, notional, and symbol-whitelist checks to every leg
        so combo orders cannot bypass the risk limits enforced on plain
        stock orders.
        """
        self._validate_combo_type(params.get("combo_type"))

        # Validate each order leg
        orders = params.get("orders", [])
        for order in orders:
            self._validate_side(order.get("side"))
            self._validate_order_type(order.get("order_type"), order.get("market"))
            if order.get("time_in_force"):
                self._validate_time_in_force(order.get("time_in_force"))
            self._validate_quantity(
                order.get("quantity"), order.get("limit_price"), order.get("market", "US")
            )
            self._validate_symbol_whitelist(order.get("symbol"))

    def validate_combo_leg(self, leg: dict) -> None:
        """Validate a single combo-order leg (US only).

        Unlike ``validate_combo_order`` (which validates a
        ``{"combo_type": ..., "orders": [...]}`` payload as a whole), this
        validates one leg dict at a time -- the shape actually produced by
        ``place_stock_combo_order``, where each leg carries its own
        ``combo_type`` (NORMAL, MASTER, STOP_PROFIT, STOP_LOSS, etc.).
        """
        self._validate_combo_type(leg.get("combo_type", "NORMAL"))
        self._validate_side(leg.get("side"))
        self._validate_order_type(leg.get("order_type"), leg.get("market"))
        if leg.get("time_in_force"):
            self._validate_time_in_force(leg.get("time_in_force"), leg.get("market"))
        self._validate_quantity(
            leg.get("quantity"), leg.get("limit_price"), leg.get("market", "US")
        )
        self._validate_symbol_whitelist(leg.get("symbol"))

    def validate_option_order(self, params: dict) -> None:
        """Validate single-leg option order parameters.

        Quantity/notional and symbol-whitelist checks apply whenever the
        caller supplies a ``quantity`` (the real order-placement call sites
        always do; validation-focused callers may omit it to test other
        fields in isolation).
        """
        self._validate_side(params.get("side"))
        self._validate_option_order_type(params.get("order_type"))
        self._validate_option_tif(params.get("time_in_force"))
        self._validate_option_price_fields(
            params.get("order_type"),
            params.get("limit_price"),
            params.get("stop_price"),
        )
        if params.get("quantity") is not None:
            self._validate_quantity(
                params.get("quantity"), params.get("limit_price"), params.get("market", "US")
            )
        self._validate_symbol_whitelist(params.get("symbol"))

    def validate_option_strategy_order(self, params: dict) -> None:
        """Validate option strategy order parameters (US only).

        Every leg's quantity is checked against max_order_quantity and the
        symbol whitelist; the overall order quantity/notional is checked
        when supplied.
        """
        strategy = params.get("strategy")
        self._validate_option_strategy(strategy)

        # Validate leg count
        legs = params.get("legs", [])
        self._validate_strategy_leg_count(strategy, len(legs))

        # Validate each leg
        for i, leg in enumerate(legs):
            self._validate_option_leg(leg, i)
            self._validate_quantity(leg.get("quantity"), None, leg.get("market", "US"))
            self._validate_symbol_whitelist(leg.get("symbol"))

        # Validate overall order quantity/notional, if supplied
        if params.get("quantity") is not None:
            self._validate_quantity(
                params.get("quantity"), params.get("limit_price"), params.get("market", "US")
            )

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
        self._validate_quantity(
            params.get("quantity"), params.get("limit_price"), params.get("market", "US")
        )
        self._validate_symbol_whitelist(params.get("symbol"))

        algo_type = params.get("algo_type")
        if algo_type is None:
            raise ValidationError("algo_type is required", field="algo_type")
        
        valid_algo_types = {"TWAP", "VWAP", "POV"}
        if algo_type not in valid_algo_types:
            raise ValidationError(
                f"Invalid algo_type '{algo_type}'. Valid values: {', '.join(sorted(valid_algo_types))}",
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
                f"Invalid side '{side}', must be one of {sorted(VALID_SIDES)}",
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
                f"quantity must be > 0, got {quantity}",
                field="quantity",
            )
        if quantity > self.server_config.max_order_quantity:
            raise ValidationError(
                f"quantity {quantity} exceeds max_order_quantity {self.server_config.max_order_quantity}",
                field="quantity",
            )
        
        # Notional value check with market-specific limits
        if price is not None:
            notional = quantity * price
            max_notional, currency = self.server_config.get_max_notional_for_market(market)
            
            if notional > max_notional:
                raise ValidationError(
                    f"Notional value {notional:.2f} {currency} "
                    f"exceeds max_order_notional_{currency.lower()} {max_notional:.2f}",
                    field="notional",
                )

    def _validate_cash_amount(self, total_cash_amount: float | None, market: str | None = None) -> None:
        """Validate a dollar-denominated (AMOUNT entrust_type) order against the notional cap.

        AMOUNT orders have no quantity to bound, so the configured notional
        limit is applied directly to total_cash_amount instead.
        """
        if total_cash_amount is None or total_cash_amount <= 0:
            raise ValidationError(
                f"total_cash_amount must be > 0, got {total_cash_amount}",
                field="total_cash_amount",
            )
        max_notional, currency = self.server_config.get_max_notional_for_market(market)
        if total_cash_amount > max_notional:
            raise ValidationError(
                f"total_cash_amount {total_cash_amount:.2f} {currency} "
                f"exceeds max_order_notional_{currency.lower()} {max_notional:.2f}",
                field="total_cash_amount",
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
                f"Symbol '{symbol}' is not in the allowed whitelist",
                field="symbol",
            )

    def _validate_entrust_type(self, entrust_type: str | None) -> None:
        """Validate entrust type if provided."""
        if entrust_type is None:
            return  # Optional, defaults to QTY in order tools
        if entrust_type not in VALID_ENTRUST_TYPES:
            raise ValidationError(
                f"Invalid entrust_type '{entrust_type}', must be one of {sorted(VALID_ENTRUST_TYPES)}",
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
                    f"Invalid order_type '{order_type}' for {market} market. "
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
                    f"Invalid time_in_force '{tif}' for {market} market. "
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
                    f"Invalid time_in_force '{tif}' for {market} market. "
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
                f"Invalid account_tax_type '{account_tax_type}', "
                f"must be one of {sorted(VALID_ACCOUNT_TAX_TYPES)}",
                field="account_tax_type",
            )

        margin_type = params.get("margin_type")
        if margin_type is not None and margin_type not in VALID_MARGIN_TYPES:
            raise ValidationError(
                f"Invalid margin_type '{margin_type}', must be one of {sorted(VALID_MARGIN_TYPES)}",
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
                f"Invalid option order_type '{order_type}', must be one of {sorted(VALID_OPTION_ORDER_TYPES)}",
                field="order_type",
            )

    def _validate_option_tif(self, tif: str | None) -> None:
        """Validate option time-in-force."""
        if tif not in VALID_OPTION_TIF:
            raise ValidationError(
                f"Invalid option time_in_force '{tif}', must be one of {sorted(VALID_OPTION_TIF)}",
                field="time_in_force",
            )

    def _validate_option_price_fields(
        self, order_type: str | None, limit_price: float | None, stop_price: float | None
    ) -> None:
        """Validate option price fields based on order type."""
        if order_type == "LIMIT" and limit_price is None:
            raise ValidationError("LIMIT option order requires 'limit_price' field", field="limit_price")
        
        if order_type in ("STOP_LOSS", "STOP_LOSS_LIMIT") and stop_price is None:
            raise ValidationError(f"{order_type} option order requires 'stop_price' field", field="stop_price")

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
                    f"Strategy '{strategy}' requires exactly {min_legs} leg(s), but {leg_count} provided",
                    field="legs",
                )
            else:
                raise ValidationError(
                    f"Strategy '{strategy}' requires {min_legs}-{max_legs} legs, but {leg_count} provided",
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


def validate_combo_leg(leg: dict, config: ServerConfig) -> None:
    """Validate a single combo-order leg (see OrderValidator.validate_combo_leg)."""
    from webull_openapi_mcp.region_config import get_region_config

    region_config = get_region_config(config.region_id)
    validator = OrderValidator(region_config, config)
    validator.validate_combo_leg(leg)


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
