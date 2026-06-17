"""MCP Server for dsa — exposes tools for AI Agent consumption.

Usage:
    python -m dsa.mcp_server

Requires: pip install mcp>=1.0.0
"""
from __future__ import annotations

import json
import logging
import sys
import traceback
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to import MCP SDK — fail gracefully with a clear message
try:
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions
    import mcp.server.stdio
    import mcp.types as types
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


def _try_get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Try to get a task from the task queue, returning None on any error."""
    try:
        from src.services.task_queue import AnalysisTaskQueue
        queue = AnalysisTaskQueue()
        task = queue.get_task(job_id)
        if task is None:
            return None
        return {
            "job_id": task.task_id,
            "stock_code": task.stock_code,
            "status": task.status,
            "progress": task.progress,
            "message": task.message or "",
        }
    except Exception:
        return None


def _try_submit_job(stock_code: str) -> Optional[Dict[str, Any]]:
    """Try to submit a stock analysis job, returning None on any error."""
    try:
        from src.services.task_queue import AnalysisTaskQueue
        queue = AnalysisTaskQueue()
        task = queue.submit_task(stock_code=stock_code)
        return {
            "job_id": task.task_id,
            "stock_code": task.stock_code,
            "status": task.status,
        }
    except Exception as e:
        return {"error": str(e)}


def _try_resolve_stock(name: str) -> Optional[Dict[str, Any]]:
    """Try to resolve a stock name to code."""
    try:
        from src.services.name_to_code_resolver import resolve_name_to_code
        code = resolve_name_to_code(name)
        if code:
            return {"query": name, "code": code}
        return None
    except Exception:
        return None


def _try_market_status() -> Dict[str, Any]:
    """Get current market status."""
    try:
        from src.core.trading_calendar import get_open_markets_today
        open_markets = get_open_markets_today()
        return {"open_markets_today": list(open_markets)}
    except Exception as e:
        return {"error": str(e)}


def _try_market_review() -> Dict[str, Any]:
    """Run a market review across open markets."""
    try:
        from src.config import get_config
        from src.core.pipeline import StockAnalysisPipeline

        config = get_config()
        pipeline = StockAnalysisPipeline(config=config)
        results = pipeline.run_market_review()
        return {"status": "completed", "markets_analyzed": len(results) if results else 0}
    except Exception as e:
        return {"error": str(e)}


def _try_analyze_sync(stock_code: str) -> Dict[str, Any]:
    """Run a synchronous stock analysis and return results."""
    try:
        from src.services.analyzer_service import analyze_stock
        result = analyze_stock(stock_code)
        if result is None:
            return {"error": "Analysis returned no result"}
        return {
            "stock_code": result.code,
            "stock_name": result.name or "",
            "advice": result.operation_advice or "",
            "score": result.sentiment_score or 0,
            "trend": result.trend_prediction or "",
        }
    except Exception as e:
        return {"error": str(e)}


def _try_list_strategies() -> List[Dict[str, str]]:
    """List available trading strategies."""
    try:
        from pathlib import Path
        import yaml

        strategies_dir = Path("strategies")
        if not strategies_dir.exists():
            return []
        result = []
        for f in sorted(strategies_dir.glob("*.yml")):
            try:
                data = yaml.safe_load(f.read_text(encoding="utf-8"))
                name = data.get("name", "") or data.get("id", f.stem)
                desc = data.get("description", "") or ""
                result.append({"id": f.stem, "name": name, "description": desc})
            except Exception:
                result.append({"id": f.stem, "name": f.stem, "description": ""})
        return result
    except Exception as e:
        return [{"error": str(e)}]


def _try_stock_quote(stock_code: str) -> Dict[str, Any]:
    """Get real-time stock quote snapshot."""
    try:
        from src.services.analyzer_service import get_stock_quote
        quote = get_stock_quote(stock_code)
        if quote is None:
            return {"error": "Quote not available"}
        return {
            "stock_code": stock_code,
            "price": quote.get("price", 0),
            "change": quote.get("change", 0),
            "change_pct": quote.get("change_pct", 0),
            "volume": quote.get("volume", 0),
            "high": quote.get("high", 0),
            "low": quote.get("low", 0),
            "open": quote.get("open", 0),
            "pre_close": quote.get("pre_close", 0),
        }
    except Exception as e:
        return {"error": str(e)}


# ---- Stock Pool helpers ----

def _try_pool_list(active_only: bool = True) -> Dict[str, Any]:
    """List stock pools."""
    try:
        from src.services.stock_pool_service import StockPoolService
        service = StockPoolService()
        pools = service.list_pools(active_only=active_only)
        return {"pools": pools, "count": len(pools)}
    except Exception as e:
        return {"error": str(e)}


def _try_pool_create(name: str, description: str = "", tags: str = "") -> Dict[str, Any]:
    """Create a stock pool."""
    try:
        from src.services.stock_pool_service import StockPoolService
        service = StockPoolService()
        pool = service.create_pool(name, description, tags)
        if pool is None:
            return {"error": f"Pool '{name}' already exists"}
        return {"pool": pool, "status": "created"}
    except Exception as e:
        return {"error": str(e)}


def _try_pool_delete(pool_id: int) -> Dict[str, Any]:
    """Delete a stock pool."""
    try:
        from src.services.stock_pool_service import StockPoolService
        service = StockPoolService()
        success = service.delete_pool(pool_id)
        if not success:
            return {"error": f"Pool {pool_id} not found"}
        return {"status": "deleted", "pool_id": pool_id}
    except Exception as e:
        return {"error": str(e)}


def _try_pool_add_stock(pool_id: int, code: str, market: str = "cn", reason: str = "") -> Dict[str, Any]:
    """Add stock to a pool."""
    try:
        from src.services.stock_pool_service import StockPoolService
        service = StockPoolService()
        success = service.add_stock(pool_id, code, market, reason)
        if not success:
            return {"error": f"Failed to add {code} to pool {pool_id}"}
        return {"status": "added", "pool_id": pool_id, "code": code}
    except Exception as e:
        return {"error": str(e)}


def _try_pool_remove_stock(pool_id: int, code: str) -> Dict[str, Any]:
    """Remove stock from a pool."""
    try:
        from src.services.stock_pool_service import StockPoolService
        service = StockPoolService()
        success = service.remove_stock(pool_id, code)
        if not success:
            return {"error": f"Failed to remove {code} from pool {pool_id}"}
        return {"status": "removed", "pool_id": pool_id, "code": code}
    except Exception as e:
        return {"error": str(e)}


def _try_pool_list_stocks(pool_id: int) -> Dict[str, Any]:
    """List stocks in a pool."""
    try:
        from src.services.stock_pool_service import StockPoolService
        service = StockPoolService()
        stocks = service.list_stocks(pool_id)
        return {"pool_id": pool_id, "stocks": stocks, "count": len(stocks)}
    except Exception as e:
        return {"error": str(e)}


# ---- Vector Search helpers ----

def _try_semantic_search(query: str, doc_type: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """Semantic search across indexed content."""
    try:
        from src.services.vector_search_service import VectorSearchService
        svc = VectorSearchService()
        results = svc.search(query, doc_type=doc_type, top_k=limit)
        return {
            "query": query,
            "results": [
                {
                    "doc_type": r.doc_type,
                    "doc_id": r.doc_id,
                    "text": r.text[:200],
                    "score": r.score,
                    "source_table": r.source_table,
                }
                for r in results
            ],
            "count": len(results),
        }
    except Exception as e:
        return {"error": str(e)}


def _try_vector_status() -> Dict[str, Any]:
    """Get vector index status."""
    try:
        from src.services.vector_search_service import VectorSearchService
        svc = VectorSearchService()
        return svc.index_status()
    except Exception as e:
        return {"error": str(e)}


def _try_rebuild_index(doc_type: Optional[str] = None) -> Dict[str, Any]:
    """Rebuild vector index."""
    try:
        from src.services.vector_search_service import VectorSearchService
        svc = VectorSearchService()
        types = [doc_type] if doc_type else None
        return svc.rebuild_index(doc_types=types)
    except Exception as e:
        return {"error": str(e)}


# ---- History helpers ----

def _try_history_stats() -> Dict[str, Any]:
    """Get history statistics."""
    try:
        from src.services.history_retention_service import HistoryRetentionService
        svc = HistoryRetentionService()
        return svc.get_stats()
    except Exception as e:
        return {"error": str(e)}


def _try_history_export(days: int = 30, code: Optional[str] = None) -> Dict[str, Any]:
    """Export analysis history as JSON."""
    try:
        from src.services.history_retention_service import HistoryRetentionService
        svc = HistoryRetentionService()
        data = svc.export_analysis_json(days=days, code=code)
        parsed = json.loads(data)
        return {"records": parsed, "count": len(parsed)}
    except Exception as e:
        return {"error": str(e)}


def _try_history_prune(older_than_days: int, code: Optional[str] = None) -> Dict[str, Any]:
    """Prune old analysis history."""
    try:
        from src.services.history_retention_service import HistoryRetentionService
        svc = HistoryRetentionService()
        count = svc.prune_analysis(older_than_days=older_than_days, code=code)
        return {"deleted": count, "older_than_days": older_than_days}
    except Exception as e:
        return {"error": str(e)}


if MCP_AVAILABLE:
    server = Server("dsa")


    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available MCP tools."""
        return [
            types.Tool(
                name="analyze_stock",
                description="Submit a stock analysis job asynchronously. Returns a job_id immediately. Use check_job_status to poll for completion.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "stock_code": {
                            "type": "string",
                            "description": "Stock code (e.g. 600519, HK00700, AAPL)",
                        }
                    },
                    "required": ["stock_code"],
                },
            ),
            types.Tool(
                name="check_job_status",
                description="Check the status and progress of an analysis job by job_id.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "Job ID returned by analyze_stock",
                        }
                    },
                    "required": ["job_id"],
                },
            ),
            types.Tool(
                name="resolve_stock",
                description="Resolve a stock name or alias to its trading code (e.g. 茅台 → 600519, tencent → hk00700).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Stock name in Chinese or English",
                        }
                    },
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="market_status",
                description="Get current market status showing which markets (cn/hk/us) are open today.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="run_market_review",
                description="Run a full market review across all open markets. Takes 1-3 minutes. Returns summary of markets analyzed.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="run_analysis_sync",
                description="Run a stock analysis synchronously and return results. Takes 1-3 minutes. Use this instead of analyze_stock+check_job_status when you can wait for results.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "stock_code": {
                            "type": "string",
                            "description": "Stock code (e.g. 600519, HK00700, AAPL)",
                        }
                    },
                    "required": ["stock_code"],
                },
            ),
            types.Tool(
                name="list_strategies",
                description="List all available trading strategies with their names and descriptions.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="get_stock_quote",
                description="Get a real-time stock quote snapshot including price, change, volume, high, low.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "stock_code": {
                            "type": "string",
                            "description": "Stock code (e.g. 600519, HK00700, AAPL)",
                        }
                    },
                    "required": ["stock_code"],
                },
            ),
            # ---- Stock Pool tools ----
            types.Tool(
                name="pool_list",
                description="List all stock pools (watchlists) with their names, tags, and member counts.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_only": {
                            "type": "boolean",
                            "description": "Only return active pools (default: true)",
                        }
                    },
                },
            ),
            types.Tool(
                name="pool_create",
                description="Create a new named stock pool (watchlist).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Pool name"},
                        "description": {"type": "string", "description": "Optional description"},
                        "tags": {"type": "string", "description": "Optional comma-separated tags"},
                    },
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="pool_delete",
                description="Delete a stock pool by its id.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pool_id": {"type": "integer", "description": "Pool id"},
                    },
                    "required": ["pool_id"],
                },
            ),
            types.Tool(
                name="pool_add_stock",
                description="Add a stock to a pool. Idempotent.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pool_id": {"type": "integer", "description": "Pool id"},
                        "code": {"type": "string", "description": "Stock code (e.g. 600519, AAPL)"},
                        "market": {"type": "string", "description": "Market: cn (default), hk, us"},
                        "reason": {"type": "string", "description": "Optional reason for adding"},
                    },
                    "required": ["pool_id", "code"],
                },
            ),
            types.Tool(
                name="pool_remove_stock",
                description="Remove a stock from a pool.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pool_id": {"type": "integer", "description": "Pool id"},
                        "code": {"type": "string", "description": "Stock code to remove"},
                    },
                    "required": ["pool_id", "code"],
                },
            ),
            types.Tool(
                name="pool_list_stocks",
                description="List all stocks in a pool with names and sectors.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pool_id": {"type": "integer", "description": "Pool id"},
                    },
                    "required": ["pool_id"],
                },
            ),
            # ---- Semantic Search ----
            types.Tool(
                name="semantic_search",
                description="Search across all indexed stock analysis, news, and conversations using natural language. Returns ranked results with similarity scores.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Natural language search query"},
                        "doc_type": {
                            "type": "string",
                            "description": "Optional: filter by document type (analysis, news, conversation). Omit to search all.",
                        },
                        "limit": {"type": "integer", "description": "Max results (default 10)"},
                    },
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="vector_index_status",
                description="Get vector index statistics — total chunks, counts by document type, and embedding provider info.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="vector_rebuild_index",
                description="Rebuild vector index from metadata. Optional: specify doc_type to rebuild only one type.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "doc_type": {
                            "type": "string",
                            "description": "Optional: only rebuild this document type (analysis, news, conversation)",
                        },
                    },
                },
            ),
            # ---- History tools ----
            types.Tool(
                name="history_stats",
                description="Get history statistics — count of analyses, conversations, and date range.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="history_export",
                description="Export analysis history as JSON.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days": {"type": "integer", "description": "How many days back (default 30)"},
                        "code": {"type": "string", "description": "Optional stock code filter"},
                    },
                },
            ),
            types.Tool(
                name="history_prune",
                description="Delete analysis history older than N days.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "older_than_days": {"type": "integer", "description": "Delete records older than this many days"},
                        "code": {"type": "string", "description": "Optional stock code filter"},
                    },
                    "required": ["older_than_days"],
                },
            ),
        ]


    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> list[types.TextContent]:
        """Handle tool execution."""
        if not arguments:
            arguments = {}

        try:
            if name == "analyze_stock":
                stock_code = arguments.get("stock_code", "")
                if not stock_code:
                    return [types.TextContent(type="text", text=json.dumps({"error": "stock_code required"}))]
                result = _try_submit_job(stock_code)
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            elif name == "check_job_status":
                job_id = arguments.get("job_id", "")
                if not job_id:
                    return [types.TextContent(type="text", text=json.dumps({"error": "job_id required"}))]
                result = _try_get_job(job_id)
                if result is None:
                    return [types.TextContent(type="text", text=json.dumps({"error": "Job not found"}))]
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            elif name == "resolve_stock":
                stock_name = arguments.get("name", "")
                result = _try_resolve_stock(stock_name)
                if result is None:
                    return [types.TextContent(type="text", text=json.dumps({"error": "Could not resolve stock name"}))]
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            elif name == "market_status":
                result = _try_market_status()
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            elif name == "run_market_review":
                result = _try_market_review()
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            elif name == "run_analysis_sync":
                stock_code = arguments.get("stock_code", "")
                if not stock_code:
                    return [types.TextContent(type="text", text=json.dumps({"error": "stock_code required"}))]
                result = _try_analyze_sync(stock_code)
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            elif name == "list_strategies":
                result = _try_list_strategies()
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            elif name == "get_stock_quote":
                stock_code = arguments.get("stock_code", "")
                if not stock_code:
                    return [types.TextContent(type="text", text=json.dumps({"error": "stock_code required"}))]
                result = _try_stock_quote(stock_code)
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            # ---- Stock Pool tools ----
            elif name == "pool_list":
                active_only = arguments.get("active_only", True)
                result = _try_pool_list(active_only)
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            elif name == "pool_create":
                pool_name = arguments.get("name", "")
                if not pool_name:
                    return [types.TextContent(type="text", text=json.dumps({"error": "name required"}))]
                result = _try_pool_create(
                    pool_name,
                    arguments.get("description", ""),
                    arguments.get("tags", ""),
                )
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            elif name == "pool_delete":
                pool_id = arguments.get("pool_id", 0)
                result = _try_pool_delete(int(pool_id))
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            elif name == "pool_add_stock":
                pool_id = arguments.get("pool_id", 0)
                code = arguments.get("code", "")
                if not code:
                    return [types.TextContent(type="text", text=json.dumps({"error": "code required"}))]
                result = _try_pool_add_stock(
                    int(pool_id),
                    code,
                    arguments.get("market", "cn"),
                    arguments.get("reason", ""),
                )
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            elif name == "pool_remove_stock":
                pool_id = arguments.get("pool_id", 0)
                code = arguments.get("code", "")
                if not code:
                    return [types.TextContent(type="text", text=json.dumps({"error": "code required"}))]
                result = _try_pool_remove_stock(int(pool_id), code)
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            elif name == "pool_list_stocks":
                pool_id = arguments.get("pool_id", 0)
                result = _try_pool_list_stocks(int(pool_id))
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            # ---- Semantic Search ----
            elif name == "semantic_search":
                query = arguments.get("query", "")
                if not query:
                    return [types.TextContent(type="text", text=json.dumps({"error": "query required"}))]
                doc_type = arguments.get("doc_type")
                limit = int(arguments.get("limit", 10))
                result = _try_semantic_search(query, doc_type, limit)
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            elif name == "vector_index_status":
                result = _try_vector_status()
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            elif name == "vector_rebuild_index":
                doc_type = arguments.get("doc_type")
                result = _try_rebuild_index(doc_type)
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            # ---- History tools ----
            elif name == "history_stats":
                result = _try_history_stats()
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            elif name == "history_export":
                days = int(arguments.get("days", 30))
                code = arguments.get("code")
                result = _try_history_export(days=days, code=code)
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            elif name == "history_prune":
                older_than_days = int(arguments.get("older_than_days", 0))
                if older_than_days <= 0:
                    return [types.TextContent(type="text", text=json.dumps({"error": "older_than_days required"}))]
                code = arguments.get("code")
                result = _try_history_prune(older_than_days, code)
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            else:
                return [types.TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

        except Exception as e:
            return [types.TextContent(type="text", text=json.dumps({"error": str(e), "traceback": traceback.format_exc()}))]


    async def run_server() -> None:
        """Run the MCP server over stdio."""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="dsa",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


    def main() -> None:
        """Entry point."""
        import asyncio
        logging.basicConfig(level=logging.INFO, stream=sys.stderr)
        asyncio.run(run_server())


    if __name__ == "__main__":
        main()

else:
    def main() -> None:
        """Fallback entry when MCP SDK is not installed."""
        print(json.dumps({
            "status": "error",
            "error": {
                "code": "MCP_SDK_MISSING",
                "message": "MCP SDK is not installed. Run: pip install mcp>=1.0.0",
                "retryable": True,
            },
        }, ensure_ascii=False, indent=2))
        sys.exit(1)


    if __name__ == "__main__":
        main()
