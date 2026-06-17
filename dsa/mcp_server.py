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
