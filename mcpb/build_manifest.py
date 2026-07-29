"""Generate manifest.json (and pyproject.toml) for the Webull OpenAPI MCPB bundle.

Everything is derived from the *installed* `webull-openapi-mcp` package so the
bundle never drifts from what users actually run:

  - version        -> importlib.metadata.version("webull-openapi-mcp")
  - python support -> the package's own Requires-Python
  - tools list     -> the live server's registered tools

Typical use (see build.sh, which wires this up end to end):

    python build_manifest.py

Overrides are available for edge cases:

    python build_manifest.py --version 1.2.0 --python-requires ">=3.11,<3.13"
    python build_manifest.py --tools /tmp/wbtools.json   # use a pre-extracted list
    python build_manifest.py --no-pyproject              # only rewrite manifest.json
"""

from __future__ import annotations

import argparse
import json
from importlib import metadata
from pathlib import Path

PACKAGE = "webull-openapi-mcp"
# Fallback Python constraint if the installed package exposes none.
DEFAULT_PYTHON_REQUIRES = ">=3.10,<3.13"


def detect_version(override: str | None) -> str:
    if override:
        return override
    return metadata.version(PACKAGE)


def detect_python_requires(override: str | None) -> str:
    if override:
        return override
    try:
        value = metadata.metadata(PACKAGE).get("Requires-Python")
    except metadata.PackageNotFoundError:
        value = None
    return value or DEFAULT_PYTHON_REQUIRES


def _tool_entry_from_dict(t: dict) -> dict:
    """Normalize a tool dict, guaranteeing an object-typed inputSchema.

    Smithery's release validation requires every tool to carry an inputSchema
    object, so we never emit a tool without one.
    """
    entry: dict = {"name": t["name"]}
    if t.get("description"):
        entry["description"] = str(t["description"]).strip()
    schema = t.get("inputSchema")
    if not isinstance(schema, dict):
        schema = {"type": "object", "properties": {}}
    entry["inputSchema"] = schema
    return entry


def load_tools(tools_path: str | None) -> list[dict]:
    """Load full tool definitions (incl. inputSchema) from JSON or the package."""
    if tools_path:
        data = json.loads(Path(tools_path).read_text(encoding="utf-8"))
        return [_tool_entry_from_dict(t) for t in data]

    import asyncio

    from webull_openapi_mcp.config import load_config
    from webull_openapi_mcp.server import build_server

    server = build_server(load_config(None))
    tools = asyncio.run(server.list_tools())

    def convert(ft) -> dict:
        # FastMCP FunctionTool -> canonical MCP Tool (exposes inputSchema).
        d = ft.to_mcp_tool().model_dump(by_alias=True, exclude_none=True)
        return _tool_entry_from_dict(d)

    return sorted((convert(t) for t in tools), key=lambda d: d["name"])


def _project_tools(tools: list[dict], include_input_schema: bool) -> list[dict]:
    """Shape the tools array per target.

    - mcpb pack (Claude Desktop / MCPB spec): only {name, description} are
      allowed; inputSchema is rejected by the packer.
    - Smithery: each tool MUST carry an inputSchema object.
    """
    out: list[dict] = []
    for t in tools:
        entry: dict = {"name": t["name"]}
        if t.get("description"):
            entry["description"] = t["description"]
        if include_input_schema:
            schema = t.get("inputSchema")
            entry["inputSchema"] = schema if isinstance(schema, dict) else {"type": "object", "properties": {}}
        out.append(entry)
    return out


def build_manifest(
    version: str,
    python_requires: str,
    tools: list[dict],
    include_input_schema: bool = False,
) -> dict:
    """Assemble the manifest dictionary."""
    tools = _project_tools(tools, include_input_schema)
    return {
        "manifest_version": "0.4",
        "name": "webull-openapi-mcp",
        "display_name": "Webull OpenAPI",
        "version": version,
        "description": (
            "Securely access Webull trading and market data from your AI assistant: "
            "real-time quotes, screeners, fundamentals, financial statements, and order "
            "placement across US, HK, JP, and more regions."
        ),
        "long_description": (
            "MCP server for the Webull OpenAPI. Provides market data (snapshots, bars, "
            "quotes, tick, NOII), screeners, watchlists, fundamentals, financial "
            "statements, and full trading (stocks, options, futures, crypto, event "
            "contracts) with per-market risk controls, symbol whitelisting, and audit "
            "logging.\n\n"
            "Requires a Webull developer account (App Key / App Secret) and a market "
            "data subscription. Defaults to the UAT sandbox environment; set the "
            "environment to `prod` for live trading. Never share your App Key / Secret "
            "with the AI model — they are injected into the server process only."
        ),
        "author": {
            "name": "Webull",
            "url": "https://github.com/webull-inc/webull-openapi-mcp",
        },
        "repository": {
            "type": "git",
            "url": "https://github.com/webull-inc/webull-openapi-mcp.git",
        },
        "homepage": "https://github.com/webull-inc/webull-openapi-mcp",
        "documentation": "https://github.com/webull-inc/webull-openapi-mcp#readme",
        "support": "https://github.com/webull-inc/webull-openapi-mcp/issues",
        "license": "Apache-2.0",
        "keywords": ["webull", "trading", "market-data", "finance", "stocks", "openapi"],
        "privacy_policies": ["https://www.webull.com/policy"],
        "server": {
            # NOTE: declared as "python" (not "uv") for cross-host compatibility.
            # Smithery's publish CLI only recognizes node/python/binary/bun and
            # rejects type "uv". Execution still goes through `uv run` below, so
            # `uv` must be available at runtime on the user's machine.
            "type": "python",
            "entry_point": "src/server.py",
            "mcp_config": {
                "command": "uv",
                "args": ["run", "--directory", "${__dirname}", "src/server.py"],
                "env": {
                    "WEBULL_APP_KEY": "${user_config.app_key}",
                    "WEBULL_APP_SECRET": "${user_config.app_secret}",
                    "WEBULL_REGION_ID": "${user_config.region_id}",
                    "WEBULL_ENVIRONMENT": "${user_config.environment}",
                    "WEBULL_TOOLSETS": "${user_config.toolsets}",
                    "WEBULL_MAX_ORDER_NOTIONAL_USD": "${user_config.max_order_notional_usd}",
                    "WEBULL_MAX_ORDER_QUANTITY": "${user_config.max_order_quantity}",
                    "WEBULL_SYMBOL_WHITELIST": "${user_config.symbol_whitelist}",
                    "WEBULL_TOKEN_DIR": "${HOME}/.webull-openapi-mcp",
                },
            },
        },
        "tools": tools,
        "tools_generated": False,
        "compatibility": {
            "claude_desktop": ">=0.12.0",
            "platforms": ["darwin", "win32", "linux"],
            "runtimes": {"python": python_requires},
        },
        "user_config": {
            "app_key": {
                "type": "string",
                "title": "Webull App Key",
                "description": "Your Webull OpenAPI App Key. Get one from your regional Webull developer portal.",
                "sensitive": True,
                "required": True,
            },
            "app_secret": {
                "type": "string",
                "title": "Webull App Secret",
                "description": "Your Webull OpenAPI App Secret. Stored securely and never exposed to the AI model.",
                "sensitive": True,
                "required": True,
            },
            "region_id": {
                "type": "string",
                "title": "Region",
                "description": "Webull region: us, hk, jp, sg, th, my, uk, mx, br, eu, za, or au.",
                "default": "us",
                "required": True,
            },
            "environment": {
                "type": "string",
                "title": "Environment",
                "description": "API environment: 'uat' (sandbox) or 'prod' (live trading). Keep 'uat' unless you intend to trade live.",
                "default": "uat",
                "required": True,
            },
            "toolsets": {
                "type": "string",
                "title": "Enabled Toolsets",
                "description": "Comma-separated toolsets to enable: account, market-data, trading, instrument. Leave empty to enable all. Set to 'account,market-data,instrument' for read-only access (no trading).",
                "required": False,
            },
            "max_order_notional_usd": {
                "type": "number",
                "title": "Max Order Value (USD)",
                "description": "Maximum notional value per order for the US market. Orders above this are rejected.",
                "default": 10000,
                "min": 0,
                "required": False,
            },
            "max_order_quantity": {
                "type": "number",
                "title": "Max Order Quantity",
                "description": "Maximum quantity (shares/contracts) allowed per order.",
                "default": 1000,
                "min": 0,
                "required": False,
            },
            "symbol_whitelist": {
                "type": "string",
                "title": "Symbol Whitelist",
                "description": "Comma-separated symbols the server is allowed to trade (e.g. AAPL,MSFT). Leave empty for no restriction.",
                "required": False,
            },
        },
    }


def build_pyproject(version: str, python_requires: str) -> str:
    """Render the bundle's pyproject.toml pinned to the exact release version."""
    return (
        "# GENERATED by build_manifest.py — do not edit by hand.\n"
        "# The host application (e.g. Claude Desktop) runs `uv run src/server.py`,\n"
        "# which reads this file, provisions a matching Python and installs the\n"
        "# dependency below from PyPI before launching the server.\n"
        "#\n"
        "# The pin below is intentionally exact so the bundle always runs the\n"
        "# released version whose tools are declared in manifest.json. Rebuild the\n"
        "# bundle (build.sh) to ship a new release.\n"
        "[project]\n"
        'name = "webull-openapi-mcp-bundle"\n'
        f'version = "{version}"\n'
        'description = "MCPB (uv runtime) bundle wrapper for Webull OpenAPI MCP Server"\n'
        f'requires-python = "{python_requires}"\n'
        "dependencies = [\n"
        f'    "webull-openapi-mcp=={version}",\n'
        "]\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tools", default=None, help="Path to a pre-extracted tools JSON file")
    parser.add_argument("--version", default=None, help="Override the bundle version")
    parser.add_argument("--python-requires", default=None, help="Override the Python constraint")
    parser.add_argument("--out", default="manifest.json", help="Output manifest path")
    parser.add_argument(
        "--target",
        choices=["mcpb", "smithery"],
        default="mcpb",
        help="mcpb: tools without inputSchema (packable by mcpb / Claude Desktop). "
        "smithery: tools with inputSchema (required by Smithery).",
    )
    parser.add_argument("--no-pyproject", action="store_true", help="Do not regenerate pyproject.toml")
    args = parser.parse_args()

    version = detect_version(args.version)
    python_requires = detect_python_requires(args.python_requires)
    tools = load_tools(args.tools)

    include_input_schema = args.target == "smithery"
    manifest = build_manifest(version, python_requires, tools, include_input_schema)
    out_path = Path(args.out)
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Wrote {out_path}: target={args.target}, version={version}, "
        f"python={python_requires}, tools={len(tools)}, inputSchema={include_input_schema}"
    )

    if not args.no_pyproject:
        pyproject_path = out_path.parent / "pyproject.toml"
        pyproject_path.write_text(build_pyproject(version, python_requires), encoding="utf-8")
        print(f"Wrote {pyproject_path}: pinned webull-openapi-mcp=={version}")


if __name__ == "__main__":
    main()
