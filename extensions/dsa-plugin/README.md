# DSA Plugin for OpenClaw

> **版本**: 0.1.0 — OpenClaw Plugin 集成，让 OpenClaw 原生调用 DSA 分析引擎。

## 目录

- [概述](#概述)
- [前置条件](#前置条件)
- [安装](#安装)
- [配置](#配置)
- [功能](#功能)
- [开发](#开发)
- [故障排查](#故障排查)

---

## 概述

DSA Plugin 是 OpenClaw 的 Finance Plugin，提供 21+ 个原生工具：
股票分析、实时行情、大盘复盘、股池管理、语义搜索、历史回溯、策略问股。

### 架构

```
OpenClaw CLI/GUI
    │
    ├── DSA Plugin (TypeScript, extensions/dsa-plugin/)
    │       │
    │       ├── index.ts          ← 插件入口，注册所有工具
    │       ├── client.ts         ← HTTP 客户端（封装 DSA REST API）
    │       ├── context.ts        ← 会话上下文（跨轮状态保持）
    │       ├── approval.ts       ← 审批流（高危操作需确认）
    │       ├── push.ts           ← 主动推送（股价预警）
    │       └── tools/index.ts    ← 21 个工具定义
    │
    └── DSA API Server (Python FastAPI, port 8000)
            │
            └── daily_stock_analysis 分析引擎
```

### 与 Skill 模式对比

| 维度 | Plugin (本插件) | 旧 Skill 模式 |
|------|----------------|---------------|
| 集成方式 | 原生 TypeScript Plugin | 通过 HTTP Skill 调用 |
| 工具数量 | 21 个结构化工具 | 1 个 HTTP 工具 (curl) |
| 参数校验 | JSON Schema 自动验证 | Skill 内手动解析 |
| 会话上下文 | 内置，支持追问 | 需自行维护 |
| 审批流 | 原生接入 | 无 |
| 主动推送 | 原生支持 | 需外部定时器 |
| 性能 | 零额外开销 | HTTP + 配置解析开销 |
| 开发语言 | TypeScript | Markdown 配置 |

---

## 前置条件

1. **DSA 服务运行中**：
   ```bash
   python main.py --serve-only
   # 或 uvicorn server:app --host 0.0.0.0 --port 8000
   ```

2. **Node.js >= 20**（当前环境: v22.15.0）

3. **OpenClaw >= 1.0.0**（支持 Plugin 加载）

---

## 安装

### 方式一：OpenClaw 内置加载（推荐）

```bash
# 1. 进入 OpenClaw 项目
cd openclaw

# 2. 将插件链接到 workspaces
pnpm add ./extensions/dsa-plugin

# 3. 重启 OpenClaw
pnpm gateway:watch
```

### 方式二：本地开发

```bash
# 编译插件
cd extensions/dsa-plugin
pnpm install
pnpm build
```

---

## 配置

在 OpenClaw 配置中设置：

```json
{
  "plugins": {
    "dsa-plugin": {
      "dsa.baseUrl": "http://localhost:8000",
      "dsa.requestTimeout": 300000,
      "dsa.push.pollInterval": 600000,
      "dsa.push.stopLossThreshold": 0.95,
      "dsa.push.takeProfitThreshold": 1.1
    }
  }
}
```

### 配置项说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `dsa.baseUrl` | `http://localhost:8000` | DSA API 服务地址 |
| `dsa.requestTimeout` | 300000 | API 请求超时 (ms) |
| `dsa.push.pollInterval` | 600000 | 预警轮询间隔 (ms) |
| `dsa.push.stopLossThreshold` | 0.95 | 止损阈值（现价/参考价） |
| `dsa.push.takeProfitThreshold` | 1.1 | 止盈阈值（现价/参考价） |

---

## 功能

### 21 个内置工具

| 类别 | 工具 | 说明 |
|------|------|------|
| **分析** | `analyze_stock` | 全量分析（技术面+新闻+LLM） |
| | `run_analysis_sync` | 同步模式分析 |
| | `check_job_status` | 查询异步任务状态 |
| **行情** | `get_stock_quote` | 实时行情 |
| | `get_stock_batch` | 批量行情 |
| | `resolve_stock` | 股票代码解析 |
| **大盘** | `market_status` | 大盘指数+板块 |
| | `run_market_review` | 大盘复盘（LLM 分析） |
| **股池** ⚠️ | `pool_list` / `pool_create` / `pool_get` | 股池增删查 |
| | `pool_add_stock` / `pool_remove_stock` | 股池股票管理 |
| | `pool_delete` | ⚠️ 删除股池（需审批） |
| **搜索** | `semantic_search` | 语义搜索 |
| | `vector_index_status` | 索引状态查询 |
| **历史** | `history_search` / `history_stats` | 历史查询 |
| | `history_export` | 历史导出 |
| | `history_prune` | ⚠️ 清理旧历史（需审批） |
| **Agent** | `agent_chat` | 策略问股 |

> ⚠️ 标记为"需审批"的操作会弹出确认卡片，用户通过后才执行。

### 会话上下文

支持跨轮对话上下文保持：
- **追问**："那五粮液呢" → 自动对比上一只分析过的股票
- **引用**："把刚才两只加入强势股池" → 自动识别最近分析结果
- **对比**：多只股票结果对比展示

### 主动推送

- 定时轮询股池行情（默认每 10 分钟）
- 跌破止损价 / 达到止盈价时自动推送告警
- 同一天同一股票不重复告警
- 推送消息可点击直接触发分析

### 审批流

以下操作需要用户确认：
- 删除股池（`pool_delete`）
- 从股池移除股票（`pool_remove_stock`）
- 清理历史数据（`history_prune`）

---

## 开发

```bash
# 安装依赖
pnpm install

# 开发模式（监听文件变化）
pnpm dev

# 构建
pnpm build

# 清理
pnpm clean
```

### 项目结构

```
extensions/dsa-plugin/
├── openclaw.plugin.json    # Plugin 元数据清单
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts            # 插件入口
│   ├── types.ts            # OpenClaw SDK 类型定义
│   ├── client.ts           # DSA HTTP 客户端
│   ├── context.ts          # 会话上下文管理
│   ├── approval.ts         # 审批流接入
│   ├── push.ts             # 主动推送
│   └── tools/
│       └── index.ts        # 21 个工具定义
└── README.md
```

---

## 故障排查

| 现象 | 可能原因 | 处理建议 |
|------|----------|----------|
| 工具调用返回 0 错误码 | DSA 未启动 | 检查 `python main.py --serve-only` |
| 超时错误 | 分析时间过长 | 增大 `dsa.requestTimeout`（≥300s） |
| 推送无消息 | 股池为空 | 先创建股池并添加股票 |
| 审批卡片不弹出 | OpenClaw 版本不支持 | 确认 OpenClaw >= 1.0.0 |
| 编译错误 | TypeScript 版本不匹配 | `pnpm install` 重新安装 |
