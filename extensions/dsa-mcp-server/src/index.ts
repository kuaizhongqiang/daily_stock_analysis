#!/usr/bin/env node
/**
 * dsa-mcp-server — MCP Server for daily_stock_analysis
 *
 * Exposes stock analysis tools via Model Context Protocol.
 * AI Agents (Claude, etc.) can use these tools to analyze stocks,
 * check market status, manage pools, and search history.
 *
 * Usage:
 *   npx dsa-mcp-server
 *   # Configure DSA_BASE_URL env var (default: http://localhost:8000)
 *
 * Or add to Claude Desktop config:
 *   {
 *     "mcpServers": {
 *       "dsa": { "command": "npx", "args": ["dsa-mcp-server"] }
 *     }
 *   }
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  type Tool,
} from "@modelcontextprotocol/sdk/types.js";

// ============================================================
// HTTP Client (inline, zero deps)
// ============================================================

const BASE_URL = (process.env.DSA_BASE_URL || "http://localhost:8000").replace(/\/+$/, "");
const TIMEOUT = parseInt(process.env.DSA_REQUEST_TIMEOUT || "300000", 10);

class DsaError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
    this.name = "DsaError";
  }
}

async function dsaRequest<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT);

  try {
    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    if (!res.ok) {
      const err = (await res.json().catch(() => ({}))) as Record<string, string | undefined>;
      throw new DsaError(res.status, err.error || "unknown_error", err.message || `HTTP ${res.status}`);
    }

    return (await res.json()) as T;
  } catch (err) {
    if (err instanceof DsaError) throw err;
    if ((err as Error).name === "AbortError") {
      throw new DsaError(408, "timeout", `Request timed out after ${TIMEOUT}ms`);
    }
    throw new DsaError(0, "connection_failed", `Cannot connect to DSA at ${BASE_URL}`);
  } finally {
    clearTimeout(timeoutId);
  }
}

// ============================================================
// Tool definitions
// ============================================================

const TOOLS: Tool[] = [
  {
    name: "analyze_stock",
    description: "Full stock analysis (technical + news + LLM). Returns a complete report with action advice, trend prediction, and strategy prices. Takes 2-5 minutes.",
    inputSchema: {
      type: "object",
      properties: {
        stock_code: { type: "string", description: "Stock code (600519, hk00700, AAPL)" },
        report_type: { type: "string", enum: ["simple", "detailed", "brief"], default: "detailed" },
        force_refresh: { type: "boolean", default: false },
      },
      required: ["stock_code"],
    },
  },
  {
    name: "get_stock_quote",
    description: "Real-time stock quote: price, change, volume, high/low.",
    inputSchema: {
      type: "object",
      properties: { stock_code: { type: "string", description: "Stock code" } },
      required: ["stock_code"],
    },
  },
  {
    name: "resolve_stock",
    description: "Resolve stock name/code (e.g. 茅台 → 600519).",
    inputSchema: {
      type: "object",
      properties: { query: { type: "string", description: "Stock name or code" } },
      required: ["query"],
    },
  },
  {
    name: "market_status",
    description: "Get market overview: indices, leading sectors.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "run_market_review",
    description: "Run full market review (LLM analysis, 1-3 min).",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "check_job_status",
    description: "Check async analysis job status.",
    inputSchema: {
      type: "object",
      properties: { task_id: { type: "string", description: "Task ID from analyze_stock async mode" } },
      required: ["task_id"],
    },
  },
  {
    name: "semantic_search",
    description: "Semantic search across indexed analysis/news/conversations.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Natural language query" },
        limit: { type: "number", default: 10 },
      },
      required: ["query"],
    },
  },
  {
    name: "pool_list",
    description: "List all stock pools.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "pool_create",
    description: "Create a stock pool.",
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "Pool name" },
        description: { type: "string", description: "Optional description" },
      },
      required: ["name"],
    },
  },
  {
    name: "pool_add_stock",
    description: "Add stock to pool.",
    inputSchema: {
      type: "object",
      properties: {
        pool_id: { type: "string", description: "Pool ID" },
        stock_code: { type: "string", description: "Stock code" },
      },
      required: ["pool_id", "stock_code"],
    },
  },
  {
    name: "pool_remove_stock",
    description: "Remove stock from pool.",
    inputSchema: {
      type: "object",
      properties: {
        pool_id: { type: "string", description: "Pool ID" },
        stock_code: { type: "string", description: "Stock code" },
      },
      required: ["pool_id", "stock_code"],
    },
  },
  {
    name: "pool_delete",
    description: "Delete a pool and all its stock relations.",
    inputSchema: {
      type: "object",
      properties: { pool_id: { type: "string", description: "Pool ID" } },
      required: ["pool_id"],
    },
  },
  {
    name: "history_search",
    description: "Search analysis history.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Search keywords" },
        limit: { type: "number", default: 20 },
      },
      required: ["query"],
    },
  },
  {
    name: "history_stats",
    description: "Get history statistics.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "history_prune",
    description: "Delete analysis history older than N days.",
    inputSchema: {
      type: "object",
      properties: { older_than_days: { type: "number", default: 90 } },
    },
  },
  {
    name: "agent_chat",
    description: "Strategy-based stock Q&A via Agent. Requires DSA AGENT_MODE=true.",
    inputSchema: {
      type: "object",
      properties: {
        message: { type: "string", description: "Question like '用缠论分析 600519'" },
        session_id: { type: "string", description: "Optional session ID for multi-turn" },
      },
      required: ["message"],
    },
  },
];

// ============================================================
// Tool handlers
// ============================================================

async function handleTool(name: string, args: Record<string, unknown>): Promise<string> {
  try {
    switch (name) {
      // ---- Analysis ----
      case "analyze_stock": {
        if (!args.stock_code) return err("VALIDATION_ERROR", "stock_code required");
        const result = await dsaRequest("POST", "/api/v1/analysis/analyze", {
          stock_code: args.stock_code,
          report_type: args.report_type || "detailed",
          force_refresh: args.force_refresh || false,
          async_mode: false,
        });
        return ok(result);
      }
      case "check_job_status": {
        if (!args.task_id) return err("VALIDATION_ERROR", "task_id required");
        const result = await dsaRequest("GET", `/api/v1/analysis/status/${args.task_id}`);
        return ok(result);
      }

      // ---- Quotes ----
      case "get_stock_quote": {
        if (!args.stock_code) return err("VALIDATION_ERROR", "stock_code required");
        const q = await dsaRequest("GET", `/api/v1/stocks/${encodeURIComponent(String(args.stock_code))}/quote`);
        return ok(q);
      }
      case "resolve_stock": {
        if (!args.query) return err("VALIDATION_ERROR", "query required");
        const r = await dsaRequest("GET", `/api/v1/stocks/resolve?q=${encodeURIComponent(String(args.query))}`);
        return ok(r);
      }

      // ---- Market ----
      case "market_status": {
        const m = await dsaRequest("GET", "/api/v1/market/status");
        return ok(m);
      }
      case "run_market_review": {
        const m = await dsaRequest("POST", "/api/v1/market/review");
        return ok(m);
      }

      // ---- Pools ----
      case "pool_list": {
        const p = await dsaRequest("GET", "/api/v1/pools");
        return ok(Array.isArray(p) ? { pools: p } : p);
      }
      case "pool_create": {
        if (!args.name) return err("VALIDATION_ERROR", "name required");
        const p = await dsaRequest("POST", "/api/v1/pools", { name: args.name, description: args.description });
        return ok(p);
      }
      case "pool_add_stock": {
        if (!args.pool_id || !args.stock_code) return err("VALIDATION_ERROR", "pool_id and stock_code required");
        const p = await dsaRequest("POST", `/api/v1/pools/${encodeURIComponent(String(args.pool_id))}/stocks`, {
          stock_code: args.stock_code,
        });
        return ok(p);
      }
      case "pool_remove_stock": {
        if (!args.pool_id || !args.stock_code) return err("VALIDATION_ERROR", "pool_id and stock_code required");
        const p = await dsaRequest("DELETE", `/api/v1/pools/${encodeURIComponent(String(args.pool_id))}/stocks`, {
          stock_code: args.stock_code,
        });
        return ok(p);
      }
      case "pool_delete": {
        if (!args.pool_id) return err("VALIDATION_ERROR", "pool_id required");
        const p = await dsaRequest("DELETE", `/api/v1/pools/${encodeURIComponent(String(args.pool_id))}`);
        return ok(p);
      }

      // ---- Search ----
      case "semantic_search": {
        if (!args.query) return err("VALIDATION_ERROR", "query required");
        const params = new URLSearchParams({ query: String(args.query) });
        if (args.limit) params.set("limit", String(args.limit));
        const s = await dsaRequest("GET", `/api/v1/search/semantic?${params}`);
        return ok(s);
      }

      // ---- History ----
      case "history_search": {
        if (!args.query) return err("VALIDATION_ERROR", "query required");
        const params = new URLSearchParams({ query: String(args.query) });
        if (args.limit) params.set("limit", String(args.limit));
        const h = await dsaRequest("GET", `/api/v1/history/search?${params}`);
        return ok(Array.isArray(h) ? { records: h } : h);
      }
      case "history_stats": {
        const s = await dsaRequest("GET", "/api/v1/history/stats");
        return ok(s);
      }
      case "history_prune": {
        const days = (args.older_than_days as number) || 90;
        const p = await dsaRequest("DELETE", `/api/v1/history/prune?older_than_days=${days}`);
        return ok(p);
      }

      // ---- Agent ----
      case "agent_chat": {
        if (!args.message) return err("VALIDATION_ERROR", "message required");
        const a = await dsaRequest("POST", "/api/v1/agent/chat", {
          message: args.message,
          session_id: args.session_id,
        });
        return ok(a);
      }

      default:
        return err("NOT_FOUND", `Unknown tool: ${name}`);
    }
  } catch (e) {
    if (e instanceof DsaError) {
      return err(e.code, e.message);
    }
    return err("INTERNAL_ERROR", (e as Error).message);
  }
}

function ok(data: unknown): string {
  return JSON.stringify({ status: "ok", data });
}

function err(code: string, message: string): string {
  return JSON.stringify({ status: "error", error: { code, message } });
}

// ============================================================
// MCP Server
// ============================================================

const server = new Server(
  { name: "dsa-mcp-server", version: "0.1.0" },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const result = await handleTool(request.params.name, (request.params.arguments ?? {}) as Record<string, unknown>);
  return {
    content: [{ type: "text" as const, text: result }],
  };
});

// ============================================================
// Entry point
// ============================================================

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("dsa-mcp-server: connected via stdio");
}

main().catch((e) => {
  console.error("dsa-mcp-server fatal:", e);
  process.exit(1);
});
