---
name: "stock_analyzer"
description: "分析股票和市场。通过 dsa MCP 工具调用股票分析、大盘复盘、行情查询等功能。"
---

# 股票分析器

通过 MCP 工具或 REST API 调用 daily_stock_analysis 的分析能力。

## 可用工具 (MCP)

| 工具名 | 说明 |
|--------|------|
| `analyze_stock` | 异步提交股票分析，返回 job_id |
| `check_job_status` | 查询分析任务状态 |
| `resolve_stock` | 解析股票名称/代码（茅台 → 600519） |
| `market_status` | 查询当前市场开市状态 |

## 工作流程

### 单股分析
1. 使用 `resolve_stock` 解析用户提到的股票名称
2. 用 `analyze_stock` 提交异步分析请求
3. 用 `check_job_status` 轮询直到 `status: completed`
4. 从结果中提取 `operation_advice`、`trend_prediction`、`sentiment_score`

### 大盘复盘
- 使用 `market_status` 获取当前市场状态
- 或通过 REST API 调用 `POST /api/v1/analysis/analyze` 提交大盘分析

### REST API（备选）
- `POST /api/v1/analysis/analyze` — 触发分析
- `GET /api/v1/analysis/status/{task_id}` — 任务状态
- `GET /api/health` — 健康检查

## 股票代码格式

| 类型 | 格式 | 示例 |
|------|------|------|
| A股 | 6位数字 | `600519`、`000001` |
| 港股 | hk + 5位数字 | `hk00700` |
| 美股 | 1-5 字母 | `AAPL`、`TSLA` |
