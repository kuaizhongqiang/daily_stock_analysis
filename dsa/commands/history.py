"""dsa history — query analysis history."""
from __future__ import annotations

from typing import Optional

import click

from ..output import JsonOutput, pass_json


@click.group(name="history")
def history() -> None:
    """Query analysis history."""


@history.command(name="ls")
@click.option("--stock", help="Filter by stock code")
@click.option("--days", type=int, default=7, help="How many days back")
@click.option("--limit", type=int, default=20)
@click.option("--decisions", help="Filter by decision action type")
@pass_json
def list_all(json_out: JsonOutput, stock: Optional[str], days: int, limit: int, decisions: Optional[str]) -> None:
    """List analysis history."""
    from src.services.history_service import HistoryService

    svc = HistoryService()
    results = svc.get_history_list(
        stock_code=stock or "",
        start_date=...,
        end_date=...,
        page=1,
        limit=limit,
    )
    json_out.ok({
        "history": results if isinstance(results, list) else [],
        "note": "History query endpoint needs refinement",
    })
