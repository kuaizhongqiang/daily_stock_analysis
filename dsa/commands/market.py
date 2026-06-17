"""dsa market — market status and review."""
from __future__ import annotations

import click

from ..output import JsonOutput, pass_json


@click.group(name="market")
def market() -> None:
    """Market status and review."""


@market.command()
@pass_json
def status(json_out: JsonOutput) -> None:
    """Get current market status (trading hours, index levels)."""
    import json as _json

    from src.core.trading_calendar import build_market_phase_context, get_open_markets_today

    open_markets = get_open_markets_today()
    phases = {}
    for m in open_markets:
        ctx = build_market_phase_context(market=m)
        phases[m] = {
            "is_open": ctx.is_trading_hours if hasattr(ctx, "is_trading_hours") else None,
            "phase": ctx.phase if hasattr(ctx, "phase") else None,
        }

    json_out.ok({
        "open_markets_today": list(open_markets),
        "market_phases": phases,
        "message": "Use `dsa market review` for detailed market review",
    })


@market.command()
@pass_json
def review(json_out: JsonOutput) -> None:
    """Run market review for all open markets."""
    from src.core.market_review import run_market_review
    from src.config import get_config

    config = get_config()
    result = run_market_review(config, dry_run=False)
    json_out.ok({
        "status": "completed" if result else "failed",
        "detail": "Market review complete" if result else "Market review returned no results",
    })


@market.command()
@click.argument("market_name", default="cn")
@pass_json
def calendar(json_out: JsonOutput, market_name: str) -> None:
    """Get trading calendar info for a market (cn/hk/us)."""
    import datetime

    from src.core.trading_calendar import get_effective_trading_date, is_market_open

    today = datetime.date.today()
    open_now = is_market_open(market_name)
    effective_date = get_effective_trading_date(market_name)

    json_out.ok({
        "market": market_name,
        "today": str(today),
        "is_open_now": open_now,
        "last_trading_day": str(effective_date) if effective_date else None,
    })
