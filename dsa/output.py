"""JSON output helper for dsa CLI."""
from __future__ import annotations

import json
import sys
from functools import update_wrapper
from typing import Optional

import click

from dsa.errors import ErrorCode, error_dict


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
    def error(
        code: ErrorCode | str,
        message: str,
        retryable: Optional[bool] = None,
    ) -> None:
        """Print error JSON with unified error format."""
        err = error_dict(code, message, retryable=retryable)
        out = {"status": "error", "error": err}
        click.echo(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(1)


def pass_json(f):
    """Decorator that passes the JsonOutput instance from context."""
    @click.pass_context
    def wrapper(ctx, *args, **kwargs):
        return ctx.invoke(f, ctx.obj["json"], *args, **kwargs)
    return update_wrapper(wrapper, f)
