"""JSON output helper for dsa CLI."""
from __future__ import annotations

import json
import sys
from functools import update_wrapper

import click


class JsonOutput:
    """JSON output helper for CLI commands."""

    @staticmethod
    def ok(data: dict, pretty: bool = True) -> None:
        """Print success JSON."""
        out = {"status": "ok", "data": data}
        if pretty:
            click.echo(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            click.echo(json.dumps(out, ensure_ascii=False))

    @staticmethod
    def error(code: str, message: str, retryable: bool = False) -> None:
        """Print error JSON."""
        out = {
            "status": "error",
            "error": {"code": code, "message": message, "retryable": retryable},
        }
        click.echo(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(1)


def pass_json(f):
    """Decorator that passes the JsonOutput instance from context."""
    @click.pass_context
    def wrapper(ctx, *args, **kwargs):
        return ctx.invoke(f, ctx.obj["json"], *args, **kwargs)
    return update_wrapper(wrapper, f)
