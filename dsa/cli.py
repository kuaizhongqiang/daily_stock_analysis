"""dsa CLI — Stock Intelligent Analysis System command-line interface.

Usage:
    dsa analyze <code>           Analyze a stock
    dsa submit <code>            Submit async analysis, returns job_id
    dsa status <job_id>          Check analysis progress
    dsa result <job_id>          Get analysis result
    dsa cancel <job_id>          Cancel a running job
    dsa jobs                     List active/recent jobs
    dsa resolve <name>           Resolve stock name to code
    dsa config                   Manage configuration
    dsa market                   Market status and review
    dsa sources                  Data source introspection
    dsa strategies               List/show strategies
    dsa history                  Query analysis history
    dsa signals                  Query decision signals
    dsa serve                    Start REST API server (FastAPI)
    dsa pool                     Stock pool management
    dsa vector                   Vector search
    dsa batch                    Batch operations
    dsa session                  Session management
    dsa alert                    Alert management
    dsa routines                 Routine tasks
"""
from __future__ import annotations

import json
import sys

import click

from .commands import analyze, config, resolve, market, sources, strategies, history, signals, serve, pool, vector
from .commands import session as session_cmd
from .commands import batch as batch_cmd
from .commands import alert as alert_cmd
from .commands import routines as routines_cmd
from .output import JsonOutput, pass_json


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Stock Intelligent Analysis System CLI."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = JsonOutput()


# Register commands
cli.add_command(analyze.analyze)
cli.add_command(analyze.submit)
cli.add_command(analyze.status)
cli.add_command(analyze.result)
cli.add_command(analyze.cancel)
cli.add_command(analyze.jobs)
cli.add_command(resolve.resolve)
cli.add_command(config.config)
cli.add_command(market.market)
cli.add_command(sources.sources)
cli.add_command(strategies.strategies)
cli.add_command(history.history)
cli.add_command(signals.signals)
cli.add_command(serve.serve)
cli.add_command(pool.pool)
cli.add_command(vector.vector)
cli.add_command(session_cmd.session)
cli.add_command(batch_cmd.batch)
cli.add_command(alert_cmd.alert)
cli.add_command(routines_cmd.routines)
cli.add_command(routines_cmd.run)


def main():
    """Entry point for `dsa` command."""
    cli()


if __name__ == "__main__":
    main()
