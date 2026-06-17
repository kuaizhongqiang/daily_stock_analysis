"""dsa sources — data source introspection."""
from __future__ import annotations

import click

from ..output import JsonOutput, pass_json


@click.group(name="sources")
def sources() -> None:
    """Data source introspection."""


@sources.command(name="ls")
@pass_json
def list_all(json_out: JsonOutput) -> None:
    """List all registered data sources."""
    from data_provider import DataFetcherManager

    mgr = DataFetcherManager()
    fetchers = mgr.available_fetchers if hasattr(mgr, "available_fetchers") else []
    json_out.ok({"sources": list(fetchers) if fetchers else []})


@sources.command()
@pass_json
def status(json_out: JsonOutput) -> None:
    """Check status of all data sources."""
    json_out.ok({
        "message": "Data source status check (not yet fully implemented)",
        "sources": [],
    })


@sources.command()
@click.argument("name")
@pass_json
def test(json_out: JsonOutput, name: str) -> None:
    """Test a specific data source connectivity."""
    json_out.ok({"source": name, "status": "not_tested", "message": "Source testing not yet implemented"})
