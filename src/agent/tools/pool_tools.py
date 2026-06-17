# -*- coding: utf-8 -*-
"""
Pool tools — stock pool management as agent-callable tools.

Tools:
- pool_list: list all stock pools
- pool_create: create a named stock pool
- pool_delete: delete a stock pool
- pool_add_stock: add stock(s) to a pool
- pool_remove_stock: remove stock(s) from a pool
- pool_list_stocks: list stocks in a pool
"""

import logging

from src.agent.tools.registry import ToolParameter, ToolDefinition

logger = logging.getLogger(__name__)

_pool_service = None


def _get_pool_service():
    """Lazy import for StockPoolService."""
    global _pool_service
    if _pool_service is None:
        from src.services.stock_pool_service import StockPoolService
        _pool_service = StockPoolService()
    return _pool_service


# ============================================================
# pool_list
# ============================================================

def _handle_pool_list(active_only: bool = True) -> dict:
    """List all stock pools."""
    service = _get_pool_service()
    pools = service.list_pools(active_only=active_only)
    return {
        "pools": pools,
        "count": len(pools),
    }


pool_list_tool = ToolDefinition(
    name="pool_list",
    description="List all stock pools (watchlists). Returns pool id, name, description, tags, and member count.",
    parameters=[
        ToolParameter(
            name="active_only",
            type="boolean",
            description="Only return active pools (default: true)",
            required=False,
            default=True,
        ),
    ],
    handler=_handle_pool_list,
    category="data",
)


# ============================================================
# pool_create
# ============================================================

def _handle_pool_create(name: str, description: str = "", tags: str = "") -> dict:
    """Create a named stock pool."""
    service = _get_pool_service()
    pool = service.create_pool(name, description, tags)
    if pool is None:
        return {"error": f"Pool '{name}' already exists or creation failed"}
    return {"pool": pool, "status": "created"}


pool_create_tool = ToolDefinition(
    name="pool_create",
    description="Create a new named stock pool (watchlist). Returns the created pool details.",
    parameters=[
        ToolParameter(name="name", type="string", description="Pool name, e.g. '蓝筹跟踪'"),
        ToolParameter(name="description", type="string", description="Optional description", required=False),
        ToolParameter(name="tags", type="string", description="Optional comma-separated tags, e.g. 'hot,tech'", required=False),
    ],
    handler=_handle_pool_create,
    category="data",
)


# ============================================================
# pool_delete
# ============================================================

def _handle_pool_delete(pool_id: int) -> dict:
    """Delete a stock pool."""
    service = _get_pool_service()
    success = service.delete_pool(pool_id)
    if not success:
        return {"error": f"Pool {pool_id} not found or delete failed"}
    return {"status": "deleted", "pool_id": pool_id}


pool_delete_tool = ToolDefinition(
    name="pool_delete",
    description="Delete a stock pool by its id. All member associations are removed.",
    parameters=[
        ToolParameter(name="pool_id", type="integer", description="Pool id to delete"),
    ],
    handler=_handle_pool_delete,
    category="data",
)


# ============================================================
# pool_add_stock
# ============================================================

def _handle_pool_add_stock(pool_id: int, code: str, market: str = "cn", reason: str = "") -> dict:
    """Add a stock to a pool."""
    service = _get_pool_service()
    success = service.add_stock(pool_id, code, market, reason)
    if not success:
        return {"error": f"Failed to add {code} to pool {pool_id}"}
    return {"status": "added", "pool_id": pool_id, "code": code}


pool_add_stock_tool = ToolDefinition(
    name="pool_add_stock",
    description="Add a stock to a stock pool by pool id. Idempotent — adding the same stock twice is harmless.",
    parameters=[
        ToolParameter(name="pool_id", type="integer", description="Pool id"),
        ToolParameter(name="code", type="string", description="Stock code, e.g. '600519', 'AAPL'"),
        ToolParameter(name="market", type="string", description="Market: cn (default), hk, us", required=False),
        ToolParameter(name="reason", type="string", description="Optional reason for adding", required=False),
    ],
    handler=_handle_pool_add_stock,
    category="data",
)


# ============================================================
# pool_remove_stock
# ============================================================

def _handle_pool_remove_stock(pool_id: int, code: str) -> dict:
    """Remove a stock from a pool."""
    service = _get_pool_service()
    success = service.remove_stock(pool_id, code)
    if not success:
        return {"error": f"Failed to remove {code} from pool {pool_id}"}
    return {"status": "removed", "pool_id": pool_id, "code": code}


pool_remove_stock_tool = ToolDefinition(
    name="pool_remove_stock",
    description="Remove a stock from a stock pool by pool id and stock code.",
    parameters=[
        ToolParameter(name="pool_id", type="integer", description="Pool id"),
        ToolParameter(name="code", type="string", description="Stock code to remove"),
    ],
    handler=_handle_pool_remove_stock,
    category="data",
)


# ============================================================
# pool_list_stocks
# ============================================================

def _handle_pool_list_stocks(pool_id: int) -> dict:
    """List all stocks in a pool."""
    service = _get_pool_service()
    stocks = service.list_stocks(pool_id)
    return {
        "pool_id": pool_id,
        "stocks": stocks,
        "count": len(stocks),
    }


pool_list_stocks_tool = ToolDefinition(
    name="pool_list_stocks",
    description="List all stocks in a stock pool. Returns stock code, name, market, sector, and add reason.",
    parameters=[
        ToolParameter(name="pool_id", type="integer", description="Pool id"),
    ],
    handler=_handle_pool_list_stocks,
    category="data",
)


# ============================================================
# Export all pool tools
# ============================================================

ALL_POOL_TOOLS = [
    pool_list_tool,
    pool_create_tool,
    pool_delete_tool,
    pool_add_stock_tool,
    pool_remove_stock_tool,
    pool_list_stocks_tool,
]
