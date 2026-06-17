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
from typing import Any, Dict, Optional

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


if MCP_AVAILABLE:
    server = Server("dsa")


    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available MCP tools."""
        return [
            types.Tool(
                name="analyze_stock",
                description="Submit a stock analysis job asynchronously. Returns a job_id immediately.",
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
                description="Check the status and progress of an analysis job.",
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
                description="Resolve a stock name or alias to its trading code (e.g. 茅台 → 600519).",
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
                description="Get current market status (open markets, trading hours).",
                inputSchema={
                    "type": "object",
                    "properties": {},
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
