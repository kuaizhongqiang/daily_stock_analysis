"""dsa mcp — start the MCP Server."""
from __future__ import annotations

import click

from ..output import JsonOutput, pass_json


@click.group(name="mcp")
def mcp() -> None:
    """MCP Server commands."""


@mcp.command()
@pass_json
def start(json_out: JsonOutput) -> None:
    """Start the MCP Server (stdio mode).

    The server exposes tools for AI Agent consumption:
    - analyze_stock: Submit stock analysis (async)
    - check_job_status: Check analysis progress
    - resolve_stock: Resolve stock name to code
    - market_status: Get current market status
    """
    from ..mcp_server import main as mcp_main

    click.echo("Starting dsa MCP Server in stdio mode...", err=True)
    mcp_main()
