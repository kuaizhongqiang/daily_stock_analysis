"""dsa strategies — list and use trading strategies."""
from __future__ import annotations

import click

from ..output import JsonOutput, pass_json


@click.group(name="strategies")
def strategies() -> None:
    """List/show trading strategies."""


@strategies.command(name="ls")
@pass_json
def list_all(json_out: JsonOutput) -> None:
    """List all available trading strategies."""
    from pathlib import Path

    strategies_dir = Path("strategies")
    strategy_files = sorted(strategies_dir.glob("*.yaml")) + sorted(strategies_dir.glob("*.yml"))

    result = []
    for sf in strategy_files:
        result.append({
            "name": sf.stem,
            "file": sf.name,
        })

    json_out.ok({"strategies": result, "count": len(result)})


@strategies.command()
@click.argument("name")
@pass_json
def show(json_out: JsonOutput, name: str) -> None:
    """Show details of a specific strategy."""
    from pathlib import Path

    import yaml

    strategy_file = Path(f"strategies/{name}.yaml")
    if not strategy_file.exists():
        strategy_file = Path(f"strategies/{name}.yml")
    if not strategy_file.exists():
        json_out.error("NOT_FOUND", f"Strategy '{name}' not found")

    with open(strategy_file, "r") as f:
        data = yaml.safe_load(f)

    json_out.ok({"name": name, "content": data})
