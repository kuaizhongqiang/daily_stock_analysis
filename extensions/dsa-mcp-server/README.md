# dsa-mcp-server

[![npm version](https://img.shields.io/npm/v/dsa-mcp-server)](https://www.npmjs.com/package/dsa-mcp-server)

MCP Server for [daily_stock_analysis](https://github.com/kuaizhongqiang/daily_stock_analysis). Exposes 16+ stock analysis tools via [Model Context Protocol](https://modelcontextprotocol.io) for AI Agent consumption.

## Install

```bash
npm install -g dsa-mcp-server
```

## Usage

```bash
# Set DSA API URL (default: http://localhost:8000)
export DSA_BASE_URL=http://localhost:8000

# Run MCP server over stdio
dsa-mcp
```

### Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "dsa": {
      "command": "npx",
      "args": ["dsa-mcp-server"],
      "env": {
        "DSA_BASE_URL": "http://localhost:8000"
      }
    }
  }
}
```

### Cursor / WindSurf

```json
{
  "mcpServers": {
    "dsa": {
      "command": "npx",
      "args": ["dsa-mcp-server"],
      "env": {
        "DSA_BASE_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `analyze_stock` | Full analysis (technical + news + LLM) |
| `get_stock_quote` | Real-time stock quote |
| `resolve_stock` | Resolve stock name to code |
| `market_status` | Market indices overview |
| `run_market_review` | Full market review (LLM) |
| `check_job_status` | Check async analysis status |
| `semantic_search` | Natural language search |
| `pool_list / create / add / remove / delete` | Pool management |
| `history_search / stats / prune` | History management |
| `agent_chat` | Strategy-based stock Q&A |

## Requirements

- DSA API running (`python main.py --serve-only`)
- Node.js 18+

## License

MIT
