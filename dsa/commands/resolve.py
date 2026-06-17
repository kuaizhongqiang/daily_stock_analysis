"""dsa resolve — stock name to code resolution."""
from __future__ import annotations

import click

from ..output import JsonOutput, pass_json


@click.command(name="resolve")
@click.argument("name")
@pass_json
def resolve(json_out: JsonOutput, name: str) -> None:
    """Resolve a stock name or alias to its trading code.

    Examples:

        dsa resolve 茅台          -> 600519

        dsa resolve 腾讯          -> HK00700

        dsa resolve AAPL          -> AAPL
    """
    from src.services.name_to_code_resolver import resolve_name_to_code

    code = resolve_name_to_code(name)
    if code:
        json_out.ok({"query": name, "code": code})
    else:
        json_out.error("NOT_FOUND", f"Could not resolve stock name: {name}", retryable=False)
