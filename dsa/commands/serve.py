"""dsa serve — start the REST API server (FastAPI).

Usage:
    dsa serve

Start the FastAPI server (uvicorn) on port 8000.
"""
from __future__ import annotations

import click

from ..output import JsonOutput, pass_json


@click.command(name="serve")
@pass_json
def serve(json_out: JsonOutput) -> None:
    """Start the REST API server (FastAPI / uvicorn).

    Launches the FastAPI server on http://0.0.0.0:8000.

    The server exposes:
    - GET  /api/v1/health        Health check
    - GET  /api/v1/pools/overview  Pool overview
    - POST /api/v1/stocks/batch    Batch stock quotes
    - ... (full REST API)
    """
    import uvicorn

    click.echo("Starting dsa API server on http://0.0.0.0:8000 ...", err=True)
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
