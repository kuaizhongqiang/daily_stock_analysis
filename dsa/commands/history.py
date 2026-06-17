"""dsa history — query analysis history, sessions, export, prune."""
from __future__ import annotations

from typing import Optional

import click

from ..output import JsonOutput, pass_json


@click.group(name="history")
def history() -> None:
    """Query analysis history and manage sessions."""


@history.command(name="ls")
@click.option("--stock", help="Filter by stock code")
@click.option("--days", type=int, default=7, help="How many days back")
@click.option("--limit", type=int, default=20)
@pass_json
def list_all(json_out: JsonOutput, stock: Optional[str], days: int, limit: int) -> None:
    """List analysis history."""
    try:
        from src.services.history_retention_service import HistoryRetentionService
        svc = HistoryRetentionService()
        if stock:
            results = svc.search_history(stock, days=days, limit=limit)
        else:
            results = svc.search_history("", days=days, limit=limit)
        json_out.ok({"history": results, "count": len(results)})
    except Exception as e:
        json_out.error("HISTORY_LIST_ERROR", str(e))


@history.command(name="sessions")
@click.option("--days", type=int, default=30, help="How many days back")
@click.option("--limit", type=int, default=20)
@pass_json
def list_sessions(json_out: JsonOutput, days: int, limit: int) -> None:
    """List analysis sessions."""
    try:
        from src.services.history_retention_service import HistoryRetentionService
        svc = HistoryRetentionService()
        sessions = svc.list_sessions(days=days, limit=limit)
        json_out.ok({"sessions": sessions, "count": len(sessions)})
    except Exception as e:
        json_out.error("HISTORY_SESSIONS_ERROR", str(e))


@history.command(name="search")
@click.argument("query")
@click.option("--days", type=int, default=90, help="How many days back")
@click.option("--limit", type=int, default=20)
@pass_json
def search_cmd(json_out: JsonOutput, query: str, days: int, limit: int) -> None:
    """Full-text search analysis history."""
    try:
        from src.services.history_retention_service import HistoryRetentionService
        svc = HistoryRetentionService()
        results = svc.search_history(query, days=days, limit=limit)
        json_out.ok({"query": query, "results": results, "count": len(results)})
    except Exception as e:
        json_out.error("HISTORY_SEARCH_ERROR", str(e))


@history.command(name="export")
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "csv"]), default="json")
@click.option("--days", type=int, default=30)
@click.option("--code", help="Stock code filter")
@pass_json
def export_cmd(json_out: JsonOutput, fmt: str, days: int, code: Optional[str]) -> None:
    """Export analysis history as JSON or CSV."""
    try:
        from src.services.history_retention_service import HistoryRetentionService
        svc = HistoryRetentionService()
        if fmt == "csv":
            data = svc.export_analysis_csv(days=days, code=code)
        else:
            data = svc.export_analysis_json(days=days, code=code)
        json_out.ok({"format": fmt, "data": data[:5000], "truncated": len(data) > 5000})
    except Exception as e:
        json_out.error("HISTORY_EXPORT_ERROR", str(e))


@history.command(name="prune")
@click.argument("older-than-days", type=int)
@click.option("--code", help="Stock code filter")
@pass_json
def prune_cmd(json_out: JsonOutput, older_than_days: int, code: Optional[str]) -> None:
    """Prune analysis history older than N days."""
    try:
        from src.services.history_retention_service import HistoryRetentionService
        svc = HistoryRetentionService()
        count = svc.prune_analysis(older_than_days=older_than_days, code=code)
        json_out.ok({"deleted": count, "older_than_days": older_than_days})
    except Exception as e:
        json_out.error("HISTORY_PRUNE_ERROR", str(e))


@history.command(name="stats")
@pass_json
def stats_cmd(json_out: JsonOutput) -> None:
    """Get history statistics."""
    try:
        from src.services.history_retention_service import HistoryRetentionService
        svc = HistoryRetentionService()
        stats = svc.get_stats()
        json_out.ok(stats)
    except Exception as e:
        json_out.error("HISTORY_STATS_ERROR", str(e))
