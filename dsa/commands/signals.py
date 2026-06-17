"""dsa signals — query decision signals."""
from __future__ import annotations

from typing import Optional

import click

from ..output import JsonOutput, pass_json


@click.group(name="signals")
def signals() -> None:
    """Query decision signals."""


@signals.command(name="ls")
@click.option("--stock", help="Filter by stock code")
@click.option("--all", "show_all", is_flag=True, help="Show all signals, not just active")
@click.option("--source", help="Filter by source type")
@click.option("--limit", type=int, default=20)
@pass_json
def list_all(json_out: JsonOutput, stock: Optional[str], show_all: bool, source: Optional[str], limit: int) -> None:
    """List decision signals."""
    from src.services.decision_signal_service import DecisionSignalService

    svc = DecisionSignalService()
    signals_list = svc.list_signals(
        stock_code=stock or None,
        status=None if show_all else "active",
        source_type=source or None,
        page=1,
        limit=limit,
    )
    json_out.ok({
        "signals": signals_list if isinstance(signals_list, list) else [],
    })
