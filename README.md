# Webull OpenAPI MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

MCP Server for Webull OpenAPI — enables AI assistants (Cursor, Claude Desktop, Kiro, etc.) to securely access Webull trading and market data.

---

## ⚠️ Disclaimer

The information provided by this tool is for reference only and does not constitute investment advice. Trading involves risk; please make decisions carefully.

See [DISCLAIMER.md](DISCLAIMER.md) for the full disclaimer.

---

## Features

- **Multi-Region Support** — US, HK, JP, and SG regions with region-specific order types, trading sessions, and validation
- **Market Data** — Real-time snapshots, tick data, quotes (depth), footprint, and OHLCV bars for stocks, futures, crypto, and event contracts
- **NOII Data** — Net Order Imbalance Indicator bars and snapshots for US stock opening/closing auctions
- **Screener** — Top gainers/losers and most active stocks ranking
- **Watchlist** — Create, manage, and query user watchlists and instruments (US, HK)
- **Fundamental Data** — Company profiles, analyst ratings, and target prices
- **Trading** — Place, modify, cancel orders for stocks, options, futures, crypto, and event contracts
- **Combo Orders** — OTO, OCO, OTOCO combo orders (US only)
- **Option Strategies** — Multi-leg option strategies: vertical, straddle, strangle, butterfly, condor, etc. (US only)
- **Algo Orders** — TWAP, VWAP, POV algorithmic orders (US only)
- **Risk Controls** — Market-specific notional limits (USD/HKD/CNH/JPY), quantity limits, symbol whitelist
- **Auto Account Resolution** — Automatically selects the correct account based on asset type (stock, futures, crypto, event)
- **Audit Logging** — All order operations are logged for compliance
- **2FA Support** — Interactive authentication flow for accounts with Two-Factor Authentication

---

## Example Prompts

Here are some prompts you can use with your AI assistant:

**Market Data**
- Show me AAPL's daily bars for the last 5 days
- Get a real-time snapshot for AAPL, MSFT, and GOOGL
- What's the current bid/ask for TSLA?
- Show me 1-minute tick data for NVDA
- Show me the NOII data for AAPL before market open

**Screener**
- What are today's top gainers?
- Show me the biggest losers in pre-market
- What are the most actively traded stocks right now?

**Watchlist**
- Show me all my watchlists
- Create a new watchlist called "Tech Stocks"
- Add AAPL and MSFT to my watchlist
- What stocks are in my watchlist?

**Fundamental & Analyst**
- Tell me about NVDA's company profile
- What do analysts rate AAPL?
- What's the analyst target price for TSLA?

**Account & Portfolio**
- What's my account balance and buying power?
- Show me all my current positions
- List all my linked accounts

**Stock Trading**
- Place a limit order to buy 100 shares of AAPL at $250
- Place a market order to sell 50 shares of TSLA
- Preview a limit buy order for 200 shares of MSFT at $450 before placing it

**Options Trading**
- Buy 1 AAPL call option, strike $250, expiring 2026-04-17, limit price $5.00
- Buy 1 TSLA put option, strike $200, expiring 2026-05-15

**Order Management**
- Show me my order history for the last 7 days
- What are my current open orders?
- Cancel order with ID abc123

**HK Market**
- Place an enhanced limit order to buy 100 shares of Tencent (00700) at HKD 500
- Place an at-auction limit order for 200 shares of 00700 at HKD 510

---

## Prerequisites

1. **Webull Developer Account** — Register at:
   - US: [developer.webull.com](https://developer.webull.com/apis/home)
   - HK: [developer.webull.hk](https://developer.webull.hk/apis/home)
   - JP: [developer.webull.co.jp](https://developer.webull.co.jp/)
   - SG: [developer.webull.com.sg](https://developer.webull.com.sg/apis/home)
2. **API Credentials** — Obtain your `App Key` and `App Secret`
3. **Market Data Subscription** — Subscribe to quotes for market data access:
   - US: [webullapp.com/quote](https://www.webullapp.com/quote) | [Guide](https://developer.webull.com/apis/docs/market-data-api/subscribe-quotes)
   - HK: [webullapp.hk/quote](https://www.webullapp.hk/quote) | [Guide](https://developer.webull.hk/apis/docs/market-data-api/subscribe-quotes)
   - JP: [webull.co.jp/pricing](https://www.webull.co.jp/pricing) | [Guide](https://developer.webull.co.jp/api-doc/market-data/subscribe-quotes/)
   - SG: [webull.com.sg/quote](https://www.webull.com.sg/quote) | [Guide](https://developer.webull.com.sg/apis/docs/market-data-api/subscribe-quotes)
4. **Python 3.10+**
5. **uv** (recommended) — [Install guide](https://docs.astral.sh/uv/getting-started/installation/)

---

## Installation

### Option 1: uvx (Recommended)

```bash
uvx webull-openapi-mcp serve
```

### Option 2: pip

```bash
pip install webull-openapi-mcp
webull-openapi-mcp serve
```

### Option 3: Local Development

```bash
git clone https://github.com/webull-inc/webull-openapi-mcp.git
cd webull-openapi-mcp
uv sync
uv run python -m webull_openapi_mcp serve
```

---

## Quick Start

### 1. Initialize Configuration

```bash
# If installed via pip:
webull-openapi-mcp init

# If using uvx:
uvx webull-openapi-mcp init

# If local development:
uv run python -m webull_openapi_mcp init
```

Creates a `.env` file in the current directory. Fill in your `WEBULL_APP_KEY` and `WEBULL_APP_SECRET`.

### 2. Authenticate

```bash
# If installed via pip:
webull-openapi-mcp auth

# If using uvx:
uvx webull-openapi-mcp auth

# If local development:
uv run python -m webull_openapi_mcp auth
```

For 2FA accounts: approve the request in your Webull mobile app. Token is valid for 15 days and auto-refreshes.

### 3. Start the Server

```bash
# If installed via pip:
webull-openapi-mcp serve

# If using uvx:
uvx webull-openapi-mcp serve

# If local development:
uv run python -m webull_openapi_mcp serve
```

---

## Client Configuration

### Kiro / Cursor / Claude Desktop

Add to your MCP configuration:

**Using environment variables:**

```json
{
  "mcpServers": {
    "webull": {
      "command": "uvx",
      "args": ["webull-openapi-mcp", "serve"],
      "env": {
        "WEBULL_APP_KEY": "your_app_key",
        "WEBULL_APP_SECRET": "your_app_secret",
        "WEBULL_REGION_ID": "us",
        "WEBULL_ENVIRONMENT": "prod"
      }
    }
  }
}
```

**Using .env file (local development):**

```json
{
  "mcpServers": {
    "webull": {
      "command": "uv",
      "args": [
        "run", "--directory", "/path/to/webull-openapi-mcp",
        "python", "-m", "webull_openapi_mcp", "serve",
        "--env-file", "/path/to/.env"
      ]
    }
  }
}
```

---

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `WEBULL_APP_KEY` | App Key (required) | — |
| `WEBULL_APP_SECRET` | App Secret (required) | — |
| `WEBULL_ENVIRONMENT` | `uat` (sandbox) or `prod` | `uat` |
| `WEBULL_REGION_ID` | `us`, `hk`, `jp`, or `sg` | `us` |
| `WEBULL_TOOLSETS` | Enabled tool categories (comma-separated). Valid values: `account`, `market-data`, `trading`, `instrument` | (all enabled) |
| `WEBULL_MAX_ORDER_NOTIONAL_USD` | Max order value for US market (USD) | `10000` |
| `WEBULL_MAX_ORDER_NOTIONAL_HKD` | Max order value for HK market (HKD) | `80000` |
| `WEBULL_MAX_ORDER_NOTIONAL_CNH` | Max order value for CN market (CNH) | `70000` |
| `WEBULL_MAX_ORDER_NOTIONAL_JPY` | Max order value for JP market (JPY) | `1500000` |
| `WEBULL_MAX_ORDER_QUANTITY` | Max order quantity | `1000` |
| `WEBULL_SYMBOL_WHITELIST` | Allowed symbols (comma-separated) | (no restriction) |
| `WEBULL_TOKEN_DIR` | Token storage directory | `./conf/` |
| `WEBULL_AUDIT_LOG_FILE` | Audit log file path | stderr only |
| `WEBULL_LOG_LEVEL` | SDK log level | `WARNING` |

> **Note:** `WEBULL_REGION_ID=us` represents **Webull US** ([developer.webull.com](https://developer.webull.com/apis/home)), `WEBULL_REGION_ID=hk` represents **Webull Hong Kong** ([developer.webull.hk](https://developer.webull.hk/apis/home)), `WEBULL_REGION_ID=jp` represents **Webull Japan** ([developer.webull.co.jp](https://developer.webull.co.jp/)), and `WEBULL_REGION_ID=sg` represents **Webull Singapore** ([developer.webull.com.sg](https://developer.webull.com.sg/apis/home)).

See [.env.example](.env.example) for full configuration template.

---

## Available Tools

### Market Data

| Category | Tools | Region |
|----------|-------|--------|
| **Stock** | `get_stock_tick`, `get_stock_snapshot`, `get_stock_quotes`, `get_stock_footprint`, `get_stock_bars`, `get_stock_bars_single`, `get_stock_noii_bars`, `get_stock_noii_snapshot` | US, HK, JP, SG |
| **Futures** | `get_futures_tick`, `get_futures_snapshot`, `get_futures_depth`, `get_futures_bars`, `get_futures_footprint` | US, HK |
| **Crypto** | `get_crypto_snapshot`, `get_crypto_bars` | US |
| **Event** | `get_event_tick`, `get_event_snapshot`, `get_event_depth`, `get_event_bars` | US |
| **Screener** | `get_gainers_losers`, `get_most_active` | US, HK, JP, SG |
| **Watchlist** | `get_watchlists`, `create_watchlist`, `update_watchlist`, `delete_watchlist`, `get_watchlist_instruments`, `add_watchlist_instruments`, `remove_watchlist_instruments`, `update_watchlist_instruments` | US, HK, JP, SG |

### Fundamental & Instrument

| Category | Tools | Region |
|----------|-------|--------|
| **Instrument** | `get_instruments`, `get_futures_instruments`, `get_futures_products`, `get_crypto_instruments`, `get_event_series`, `get_event_instruments`, `get_event_categories`, `get_event_events` | varies |
| **Fundamental** | `get_company_profile`, `get_analyst_rating`, `get_analyst_target_price` | US, HK, JP, SG |

### Trading

| Category | Tools | Region |
|----------|-------|--------|
| **Account** | `get_account_list` | US, HK, JP, SG |
| **Assets** | `get_account_balance`, `get_account_positions`, `get_account_position_details` (JP only) | US, HK, JP, SG |
| **Stock Order** | `place_stock_order`, `preview_stock_order`, `replace_stock_order` | US, HK, JP, SG |
| **Combo Order** | `place_stock_combo_order` (OTO/OCO/OTOCO) | US |
| **Option Order** | `place_option_single_order`, `preview_option_order`, `replace_option_order` | US, HK |
| **Option Strategy** | `place_option_strategy_order` | US |
| **Algo Order** | `place_algo_order` (TWAP/VWAP/POV) | US |
| **Futures Order** | `place_futures_order`, `replace_futures_order` | US, HK |
| **Crypto Order** | `place_crypto_order` | US |
| **Event Order** | `place_event_order`, `replace_event_order` | US |
| **Order** | `cancel_order`, `get_order_history`, `get_open_orders`, `get_order_detail` | US, HK, JP, SG |

### Region Differences

| Feature | US | HK | JP | SG |
|---------|----|----|----|----|
| Stock Trading | Yes | Yes | Yes | Yes |
| Option Trading | Yes | Yes | No | No |
| Futures Trading | Yes | Yes | No | No |
| Crypto Trading | Yes | No | No | No |
| Event Contracts | Yes | No | No | No |
| Combo Orders | Yes | No | No | No |
| Option Strategies | Yes | No | No | No |
| Algo Orders | Yes | No | No | No |
| Screener (Gainers/Losers/Active) | Yes | Yes | Yes | Yes |
| Watchlist | Yes | Yes | Yes | Yes |
| Fundamental (Company/Analyst) | Yes | Yes | Yes | Yes |
| NOII (Auction Imbalance) | Yes | Yes | Yes | Yes |
| Markets | US | US, HK, CN | US, JP | US |
| Instrument Categories | US_STOCK, US_ETF | US_STOCK, US_ETF, HK_STOCK, CN_STOCK | US_STOCK, US_ETF | US_STOCK, US_ETF |
| Order Types | LIMIT, MARKET, STOP_LOSS, STOP_LOSS_LIMIT, TRAILING_STOP_LOSS, etc. | LIMIT, MARKET, ENHANCED_LIMIT, AT_AUCTION, AT_AUCTION_LIMIT, etc. | JP market: LIMIT, MARKET — US market: LIMIT, MARKET, STOP_LOSS, STOP_LOSS_LIMIT | MARKET, LIMIT, STOP_LOSS, STOP_LOSS_LIMIT |
| Time-in-Force | DAY, GTC | US market: DAY, GTC, GTD — HK market: DAY, GTC — CN market: DAY | JP market: DAY — US market: DAY, GTC, GTD | DAY, GTC |
| Trading Sessions | ALL, CORE, NIGHT | CORE, ALL_DAY, NIGHT, ALL | CORE, ALL, NIGHT, ALL_DAY | NIGHT, ALL, CORE, ALL_DAY |
| JP Order Fields | — | — | `account_tax_type` required (GENERAL or SPECIFIC); `margin_type` (ONE_DAY or INDEFINITE) and `position_intent` optional margin-account-only fields; `close_contracts` optional | — |

> **Note:** Screener, Fundamental, and NOII currently only support querying US stock data (`US_STOCK` category). Watchlist supports US stocks and HK stocks.

---

## CLI Commands

**If installed via pip:**

```bash
webull-openapi-mcp --version                        # Show version
webull-openapi-mcp init [--env-file PATH]           # Initialize .env configuration
webull-openapi-mcp init --app-key KEY --app-secret SECRET --environment prod
webull-openapi-mcp auth [--env-file PATH]           # Authenticate (2FA accounts)
webull-openapi-mcp serve [--env-file PATH]          # Start MCP server
webull-openapi-mcp status [--env-file PATH]         # Show configuration status
webull-openapi-mcp tools [--env-file PATH]          # List available tools
```

**If using uvx** (prefix with `uvx`):

```bash
uvx webull-openapi-mcp auth
uvx webull-openapi-mcp serve
uvx webull-openapi-mcp status
```

**If local development** (prefix with `uv run python -m webull_openapi_mcp`):

```bash
uv run python -m webull_openapi_mcp auth
uv run python -m webull_openapi_mcp serve
```

All commands accept `--env-file PATH` to specify a custom `.env` file location (default: `.env` in the current directory).

---

## Security

- **Never share your AK/SK with AI models** — Do not paste your App Key or App Secret into chat prompts, AI assistants, or any LLM conversation. These credentials should only be configured via environment variables or `.env` files, never exposed in plain text to the model.
- **Prefer `env` over `.env` files** — Pass credentials via the MCP client's `env` field (in `mcp.json`) rather than a `.env` file in your workspace. The `env` field injects credentials as process environment variables, which the AI model cannot access. A `.env` file in your workspace could be read by the AI assistant through IDE file access.
- **Credential isolation** — AK/SK are used only inside the MCP server process for SDK initialization and request signing. They never appear in tool outputs, logs, or error messages.
- **Review before trading** — Always review order details proposed by the AI before confirming. Use `preview_stock_order` / `preview_option_order` before placing orders.
- **Use toolset filtering** — Set `WEBULL_TOOLSETS=account,market-data` to disable trading tools entirely if you only need read-only access. Valid toolsets: `account`, `market-data`, `trading`, `instrument`.
- **Default sandbox** — The server defaults to UAT (sandbox) environment. You must explicitly set `WEBULL_ENVIRONMENT=prod` for live trading.
- **Dependency security** — `fastmcp` is pinned to version `3.0.2` and `webull-openapi-python-sdk` is pinned to `2.0.7`. Users are responsible for monitoring and updating third-party dependencies for security patches. Review release notes before upgrading.

---

## Troubleshooting

### 2FA Authentication Required

```bash
# If installed via pip:
webull-openapi-mcp auth

# If using uvx:
uvx webull-openapi-mcp auth

# If local development:
uv run python -m webull_openapi_mcp auth
```

Approve the request in your Webull app, then start the server.

### Device Not Registered

1. Open Webull mobile app, log in with your API account, complete device registration
2. Then authenticate:

```bash
# If installed via pip:
webull-openapi-mcp auth

# If using uvx:
uvx webull-openapi-mcp auth
```

### Market Data 401/403

Subscribe to quotes:
- HK: [webullapp.hk/quote](https://www.webullapp.hk/quote) | [Guide](https://developer.webull.hk/apis/docs/market-data-api/subscribe-quotes)
- US: [webullapp.com/quote](https://www.webullapp.com/quote) | [Guide](https://developer.webull.com/apis/docs/market-data-api/subscribe-quotes)
- JP: [webull.co.jp/pricing](https://www.webull.co.jp/pricing) | [Guide](https://developer.webull.co.jp/api-doc/market-data/subscribe-quotes/)
- SG: [webull.com.sg/quote](https://www.webull.com.sg/quote) | [Guide](https://developer.webull.com.sg/apis/docs/market-data-api/subscribe-quotes)

### Token Expired

```bash
rm -rf ./conf/token.txt

# Then re-authenticate:
webull-openapi-mcp auth       # pip
uvx webull-openapi-mcp auth   # uvx
```

### Windows: Garbled Characters in Error Messages

On Windows, authentication error messages may display garbled characters if the console encoding is not UTF-8. The server automatically detects the console encoding and falls back to ASCII-only output on non-UTF-8 terminals. If you still see garbled text, run:

```cmd
chcp 65001
```

This switches the Windows console to UTF-8 before starting the server.

---

## Project Structure

```
webull-openapi-mcp/
├── webull_openapi_mcp/
│   ├── __init__.py         # Package version
│   ├── __main__.py         # python -m entry point
│   ├── cli.py              # CLI commands (init, auth, serve, status, tools)
│   ├── server.py           # MCP server setup and tool registration
│   ├── sdk_client.py       # Webull SDK adapter (ApiClient, TradeClient, DataClient)
│   ├── config.py           # Configuration loading and validation
│   ├── region_config.py    # Region-specific settings (US, HK, JP, SG)
│   ├── guards.py           # Order validation (price, quantity, notional, region rules)
│   ├── audit.py            # Audit logging for order operations
│   ├── errors.py           # Exception definitions and SDK error handling
│   ├── formatters.py       # Response formatting with disclaimer
│   ├── constants.py        # Enum constants (sides, order types, strategies)
│   └── tools/
│       ├── __init__.py     # Tool registration exports
│       ├── market_data/
│       │   ├── stock.py    # Stock market data (snapshot, quotes, bars, tick, footprint, NOII)
│       │   ├── futures.py  # Futures market data
│       │   ├── crypto.py   # Crypto market data
│       │   ├── event.py    # Event contract market data
│       │   ├── screener.py # Gainers/losers, most active rankings
│       │   ├── watchlist.py# Watchlist CRUD and instrument management
│       │   └── fundamental.py # Company profile, analyst ratings/target price
│       └── trading/
│           ├── account.py       # Account list
│           ├── assets.py        # Balance, positions
│           ├── instrument.py    # Instrument lookup
│           ├── order.py         # Order query, cancel (shared across asset types)
│           ├── stock_order.py   # Stock order place, preview, replace
│           ├── option_order.py  # Option single-leg and strategy orders
│           ├── futures_order.py # Futures order place, replace
│           ├── crypto_order.py  # Crypto order place
│           └── event_order.py   # Event contract order place, replace
├── tests/                  # Unit and property-based tests
├── conf/                   # Token storage (auto-generated)
├── .env.example            # Configuration template
├── DISCLAIMER.md           # Full disclaimer
├── pyproject.toml          # Package configuration
└── LICENSE                 # Apache 2.0
```

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
