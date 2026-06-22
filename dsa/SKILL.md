---
name: "dsa-server"
description: "股票智能分析系统。通过 dsa CLI 调用分析、行情、股池、搜索、历史等功能。"
---

# DSA Server

股票智能分析系统，覆盖 A 股、港股、美股。支持多源数据抓取、技术分析、LLM 决策分析、股池管理、语义搜索。

## 安装

```bash
pip install dsa-server
```

## 可用命令

### 分析与行情

| 命令 | 说明 |
|------|------|
| `dsa analyze <code>` | 同步分析股票，等待结果 |
| `dsa submit <code>` | 异步提交分析，返回 job_id |
| `dsa status <job_id>` | 查询任务进度 |
| `dsa result <job_id>` | 获取分析结果 |
| `dsa jobs` | 列出所有任务 |
| `dsa resolve <name>` | 解析股票名称到代码 |
| `dsa market` | 大盘状态与复盘 |

### 股池管理

| 命令 | 说明 |
|------|------|
| `dsa pool create <name>` | 创建股池 |
| `dsa pool ls` | 列出股池 |
| `dsa pool add <id> <code>` | 添加股票到股池 |
| `dsa pool remove <id> <code>` | 从股池移除股票 |

### 搜索与历史

| 命令 | 说明 |
|------|------|
| `dsa vector search <query>` | 语义搜索 |
| `dsa history search <query>` | 历史搜索 |
| `dsa history stats` | 历史统计 |
| `dsa history export` | 导出历史 |

### 告警与会话

| 命令 | 说明 |
|------|------|
| `dsa alert create --stock <code> --type price --condition "p < 200"` | 创建告警 |
| `dsa session start` | 创建分析会话 |
| `dsa batch analyze --stocks <codes>` | 批量分析 |

## 启动服务

```bash
dsa-server
# 服务运行在 http://localhost:8000
```

## 数据来源

行情数据：AkShare、Tushare、Pytdx、Baostock、YFinance、LongBridge
新闻搜索：SerpAPI、Tavily、Brave
AI 模型：LM Studio（本地默认）、OpenAI、DeepSeek 等
