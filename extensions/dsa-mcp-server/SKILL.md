---
name: "dsa-mcp-server"
description: "通过 MCP 协议调用 daily_stock_analysis 分析引擎。支持股票分析、行情查询、大盘复盘、股池管理、语义搜索。"
---

# DSA MCP Server

通过 MCP 协议调用 daily_stock_analysis 的核心分析能力。

## 前置条件

- DSA 服务运行中：`python main.py --serve-only`
- 环境变量 `DSA_BASE_URL`（默认 `http://localhost:8000`）

## 可用工具

### 📊 分析与行情

| 工具名 | 说明 |
|--------|------|
| `analyze_stock` | 全量分析（技术面+新闻+LLM），返回完整报告 |
| `get_stock_quote` | 实时行情快照 |
| `resolve_stock` | 解析股票名称/代码 |

### 📈 大盘

| 工具名 | 说明 |
|--------|------|
| `market_status` | 大盘指数概况 |
| `run_market_review` | 大盘综合复盘（1-3 分钟）|

### 🏊 股池管理

| 工具名 | 说明 |
|--------|------|
| `pool_list / pool_create` | 股池列表与创建 |
| `pool_add_stock / pool_remove_stock` | 股池股票管理 |
| `pool_delete` | 删除股池 |

### 🔍 搜索与历史

| 工具名 | 说明 |
|--------|------|
| `semantic_search` | 自然语言搜索 |
| `history_search / history_stats / history_prune` | 历史管理 |

### 🤖 Agent

| 工具名 | 说明 |
|--------|------|
| `agent_chat` | 策略问股（需 AGENT_MODE=true）|

## 工作流程

1. `resolve_stock` → 解析股票代码
2. `analyze_stock` → 执行分析（2-5 分钟）
3. `semantic_search` → 搜索相关信息
4. `pool_add_stock` → 添加到股池跟踪
