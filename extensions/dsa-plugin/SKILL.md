---
name: "dsa-plugin"
description: "通过 DSA Plugin 原生工具调用股票分析、实时行情、大盘复盘、股池管理、语义搜索、历史回溯、策略问股。支持会话上下文追问、审批流、主动推送。"
---

# DSA Stock Analysis Plugin

通过 OpenClaw Plugin 原生调用 daily_stock_analysis 的 21 个结构化工具。

## 前置条件

- DSA 服务运行中：`python main.py --serve-only`
- OpenClaw >= 1.0.0
- Plugin 已安装并启用

## 可用工具

### 📊 股票分析与行情

| 工具名 | 说明 |
|--------|------|
| `analyze_stock` | 全量分析（技术面 + 新闻 + LLM），返回完整报告 |
| `run_analysis_sync` | 同步模式分析，等待完成后直接返回结果 |
| `check_job_status` | 查询异步分析任务状态 |
| `get_stock_quote` | 获取实时行情快照（价格、涨跌幅、成交量） |
| `get_stock_batch` | 批量查询多只股票实时行情 |
| `resolve_stock` | 解析股票名称/代码（"茅台" → "600519"） |

### 📈 大盘与策略

| 工具名 | 说明 |
|--------|------|
| `market_status` | 大盘指数 + 板块涨跌概况 |
| `run_market_review` | 执行大盘综合复盘（LLM 分析，1-3 分钟）|

### 🏊 股池管理

| 工具名 | 说明 |
|--------|------|
| `pool_list` / `pool_create` / `pool_get` | 股池增删查 |
| `pool_add_stock` / `pool_remove_stock` | 股池股票管理 |
| `pool_delete` | ⚠️ 删除股池（需审批确认）|

### 🔍 语义搜索

| 工具名 | 说明 |
|--------|------|
| `semantic_search` | 自然语言搜索已索引的分析、新闻、对话 |
| `vector_index_status` | 向量索引状态查询 |

### 📜 历史管理

| 工具名 | 说明 |
|--------|------|
| `history_search` / `history_stats` | 历史分析与统计 |
| `history_export` | 导出分析历史 |
| `history_prune` | ⚠️ 清理旧历史（需审批确认）|

### 🤖 Agent 策略问股

| 工具名 | 说明 |
|--------|------|
| `agent_chat` | 策略问股，支持缠论、均线金叉等高级策略 |

## 核心能力

### 会话上下文
支持跨轮对话上下文保持：
- **追问**："那五粮液呢" → 自动对比上一只分析过的标的
- **引用**："把刚才两只加入强势股池" → 识别最近分析结果
- `analyze_stock` 和 `run_analysis_sync` 自动绑定会话上下文

### 审批流
以下操作需要用户确认后才能执行：
- 删除股池（`pool_delete`）
- 从股池移除股票（`pool_remove_stock`）
- 清理历史数据（`history_prune`）

### 主动推送
- 定时轮询股池行情（默认每 10 分钟）
- 跌破止损价 / 达到止盈价时自动推送消息
- 同一天同一股票不重复告警

## 工作流程

### 单股分析
1. 调用 `analyze_stock` 或 `run_analysis_sync` 传入股票代码
2. 等待返回完整分析报告（含评分、操作建议、策略价位）
3. 追问 "那五粮液呢" → 自动对比分析

### 股池批量分析
1. 用 `pool_list` 查看现有股池
2. 用 `pool_create` 创建新股池
3. 用 `pool_add_stock` 添加股票到股池
4. 对池内股票逐一调用 `run_analysis_sync`
5. 用 `pool_remove_stock` 移除不再关注的股票

### 大盘复盘
1. 用 `market_status` 查看当前大盘概况
2. 用 `run_market_review` 执行完整复盘

### 语义搜索
1. 用 `semantic_search` 输入自然语言查询（如"白酒龙头最近表现"）
2. 按相似度排序的结果中包含原文和来源

## 错误处理

工具调用返回统一格式的错误：
```json
{
  "status": "error",
  "error": {
    "code": "NOT_FOUND",
    "message": "Stock not found",
    "retryable": false
  }
}
```

常见错误码：
- `VALIDATION_ERROR` — 参数校验失败（检查输入）
- `NOT_FOUND` — 资源不存在
- `TIMEOUT` — 分析超时（可重试）
- `CONNECTION_FAILED` — DSA 未启动（检查服务）
- `UPSTREAM_ERROR` — 数据源/LLM 错误
