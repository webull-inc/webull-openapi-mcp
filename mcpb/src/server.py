"""MCPB (uv runtime) entry point for the Webull OpenAPI MCP Server.

The host application launches this file via `uv run src/server.py`. All
configuration (App Key / Secret, region, environment, risk controls) is
provided through environment variables that the host injects from the
extension's user configuration.

This is a thin shim: it delegates to the published `webull-openapi-mcp`
package's CLI and starts the stdio MCP server via the `serve` subcommand.
"""

from __future__ import annotations

import sys

from webull_openapi_mcp.cli import main


def run() -> None:
    """Start the MCP server in stdio mode.

    `uv run src/server.py` invokes this script with no extra CLI arguments,
    so we inject the `serve` subcommand expected by the underlying Click CLI.
    """
    if len(sys.argv) == 1:
        sys.argv.append("serve")
    main()


if __name__ == "__main__":
    run()
