# -*- coding: utf-8 -*-
"""
CLI pool commands — manage stock pools (watchlists).
"""
from __future__ import annotations

import json
import sys

import click

from dsa.output import JsonOutput, pass_json


@click.group(name="pool")
def pool() -> None:
    """Manage stock pools (watchlists)."""


@pool.command(name="list")
@click.option("--all", "show_all", is_flag=True, help="Show all pools including inactive")
@pass_json
def pool_list(json_out: JsonOutput, show_all: bool) -> None:
    """List all stock pools."""
    try:
        from src.services.stock_pool_service import StockPoolService

        service = StockPoolService()
        pools = service.list_pools(active_only=not show_all)
        json_out.ok({"pools": pools, "count": len(pools)})
    except Exception as e:
        json_out.error("POOL_LIST_ERROR", str(e))


@pool.command(name="create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Pool description")
@click.option("--tags", "-t", default="", help="Comma-separated tags")
@pass_json
def pool_create(json_out: JsonOutput, name: str, description: str, tags: str) -> None:
    """Create a new stock pool."""
    try:
        from src.services.stock_pool_service import StockPoolService

        service = StockPoolService()
        pool = service.create_pool(name, description, tags)
        if pool is None:
            json_out.error("POOL_EXISTS", f"Pool '{name}' already exists or creation failed")
        else:
            json_out.ok({"pool": pool, "status": "created"})
    except Exception as e:
        json_out.error("POOL_CREATE_ERROR", str(e))


@pool.command(name="delete")
@click.argument("pool-id", type=int)
@pass_json
def pool_delete(json_out: JsonOutput, pool_id: int) -> None:
    """Delete a stock pool."""
    try:
        from src.services.stock_pool_service import StockPoolService

        service = StockPoolService()
        success = service.delete_pool(pool_id)
        if success:
            json_out.ok({"status": "deleted", "pool_id": pool_id})
        else:
            json_out.error("POOL_NOT_FOUND", f"Pool {pool_id} not found or delete failed")
    except Exception as e:
        json_out.error("POOL_DELETE_ERROR", str(e))


@pool.command(name="add")
@click.argument("pool-id", type=int)
@click.argument("codes", nargs=-1, required=True)
@click.option("--market", "-m", default="cn", help="Market: cn (default), hk, us")
@click.option("--reason", "-r", default="", help="Reason for adding")
@pass_json
def pool_add(json_out: JsonOutput, pool_id: int, codes: tuple[str], market: str, reason: str) -> None:
    """Add stock(s) to a pool."""
    try:
        from src.services.stock_pool_service import StockPoolService

        service = StockPoolService()
        results = []
        for code in codes:
            ok = service.add_stock(pool_id, code, market, reason)
            results.append({"code": code, "success": ok})
        json_out.ok({"pool_id": pool_id, "results": results})
    except Exception as e:
        json_out.error("POOL_ADD_ERROR", str(e))


@pool.command(name="remove")
@click.argument("pool-id", type=int)
@click.argument("codes", nargs=-1, required=True)
@pass_json
def pool_remove(json_out: JsonOutput, pool_id: int, codes: tuple[str]) -> None:
    """Remove stock(s) from a pool."""
    try:
        from src.services.stock_pool_service import StockPoolService

        service = StockPoolService()
        results = []
        for code in codes:
            ok = service.remove_stock(pool_id, code)
            results.append({"code": code, "success": ok})
        json_out.ok({"pool_id": pool_id, "results": results})
    except Exception as e:
        json_out.error("POOL_REMOVE_ERROR", str(e))


@pool.command(name="stocks")
@click.argument("pool-id", type=int)
@pass_json
def pool_stocks(json_out: JsonOutput, pool_id: int) -> None:
    """List stocks in a pool."""
    try:
        from src.services.stock_pool_service import StockPoolService

        service = StockPoolService()
        stocks = service.list_stocks(pool_id)
        json_out.ok({"pool_id": pool_id, "stocks": stocks, "count": len(stocks)})
    except Exception as e:
        json_out.error("POOL_STOCKS_ERROR", str(e))


if __name__ == "__main__":
    pool()
