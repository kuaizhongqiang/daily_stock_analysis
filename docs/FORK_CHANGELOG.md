# Fork 变更文档

## 概述

本仓库是基于 [ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis)（MIT License）的工具库 Fork。

**核心理念**: 从面向人的全功能平台 → 面向 AI Agent 的分析工具库。

原始项目是一个功能完备的 AI 股票分析平台，包含 Web UI、桌面端、多 Bot 渠道、通知推送、定时任务等。本 Fork 剥离了所有平台层和自主行为，保留核心分析引擎，由 AI Agent 通过 CLI / MCP / OpenClaw Skill 按需调用。

---

## 变更清单

### 1. 平台层剥离

#### 1.1 移除 Web UI（2026-06）
- 删除 `apps/dsa-web/` 全部前端代码（React + Vite + Tailwind + TypeScript）
- 约 300+ 文件，包含组件、页面、状态管理、API 客户端、i18n、主题系统
- 受影响测试：所有前端测试已删除

#### 1.2 移除桌面端（2026-06）
- 删除 `apps/dsa-desktop/` 全部桌面端代码（Electron）
- 包含主进程、预加载脚本、安装程序配置
- 受影响测试：桌面端测试已删除

#### 1.3 移除 Bot 渠道（2026-06）
- 删除 `bot/` 整个目录
  - `commands/`（10 个命令文件）
  - `platforms/`（5 个平台文件：钉钉、飞书、Discord）
  - `dispatcher.py`、`handler.py`、`models.py` 等
- 删除 `docs/bot-command.md`、`docs/bot-command_EN.md`、`docs/bot/` 目录
- 删除 10 个 bot 相关测试文件

#### 1.4 移除通知推送（2026-06）
- 删除 `src/notification_sender/` 全部 12 个 sender：
  - 企业微信、飞书、Telegram、邮件、Pushover、ntfy、Gotify
  - Discord、Slack、Server酱3、AstrBot、自定义 Webhook
- 删除 `src/notification.py`、`src/notification_routing.py`
- 删除 `src/notification_capabilities.py`、`src/notification_contracts.py`
- 删除 `src/notification_noise.py`、`src/notification_utils.py`
- 清理 `main.py`、`pipeline.py`、`config.py` 中通知相关代码
- 删除 10+ 通知相关测试文件
- 删除 `docs/notifications.md`

#### 1.5 移除报告模板
- 删除 `templates/` 全部 Jinja2 模板
- 删除 `src/md2img.py`（Markdown 转图片）

#### 1.6 移除 WebUI 相关
- 删除 `src/webui_frontend.py`、`webui.py`
- 删除 `docs/deploy-webui-cloud.md`、`docs/settings-help.md`

#### 1.7 移除桌面端文档
- 删除 `docs/desktop-package.md`

#### 1.8 其他移除
- 删除 `改动清单.md`（内部开发笔记）
- 删除 `docs/beginner-client-setup.md`
- 删除 `docs/docker/zeabur-deployment.md`
- 删除 `docs/assets/`（全部图片和设计资源）
- 删除 `docs/README_CHT.md`、`docs/README_EN.md`（上游镜像文档）

### 2. 自主行为移除

#### 2.1 删除自主工作流
- `auto-tag.yml` — 自动版本号标记
- `create-release.yml` — 自动 Release 发布
- `stale.yml` — 自动标记陈旧 Issue
- `.github/release.yml` — release-drafter 配置

#### 2.2 剥离定时触发
- `00-daily-analysis.yml`：删除 cron 定时触发，保留 workflow_dispatch
- `network-smoke.yml`：删除 cron 定时触发，保留 workflow_dispatch
- `main.py`：删除 `--schedule` 参数及全部定时模式代码
- 删除 `_resolve_scheduled_stock_codes`、`_reload_runtime_config`、`_build_schedule_time_provider` 函数

### 3. 默认 LLM 切换为本地 LM Studio

#### 3.1 精简 .env.example（814 行 → 145 行）
- 默认 LLM 改为 LM Studio（`http://localhost:1234/v1`），无需云 API Key
- 删除 15+ 云 LLM 厂商配置：Gemini、DeepSeek、AIHubMix、Anthropic、OpenAI
  Anspire、Moonshot、DashScope、Zhipu、MiniMax、SiliconFlow
  OpenRouter、Volcengine、Ollama、Mimo
- 删除所有多渠道模板（`LLM_*_PROTOCOL/BASE_URL/API_KEY/MODELS/ENABLED`）
- 删除 12+ 通知渠道配置（企业微信、飞书、Telegram、邮件等）
- 删除 WebUI、登录认证、定时任务、Markdown 转图片等配置

#### 3.2 精简 Dockerfile
- 删除 `COPY bot/ ./bot/`（Bot 已移除）
- 删除 `COPY --from=web-builder`（多阶段前端构建已移除）
- 删除 `WEBUI_HOST` 环境变量
- 默认 CMD 改为 `--serve-only`

#### 3.3 更新项目文档
- `CLAUDE.md`：更新架构图、目录映射、常用命令
- `AGENTS.md`：删除 Web/Desktop 验证矩阵，替换为 CLI/MCP 验证
- `README.md`：Fork 说明 + LM Studio 默认 + dsa CLI 用法

### 4. 新增内容

#### 4.1 MCP 服务器与 CLI 工具（dsa/）
新增 `dsa/` Python 包，提供：
- **CLI 工具**（Click）：`analyze`、`submit`、`status`、`resolve`、`market`、`mcp` 等 12+ 命令
- **MCP Server**（stdio）：暴露 4 个工具
  - `analyze_stock` — 异步提交分析
  - `check_job_status` — 查询任务状态
  - `resolve_stock` — 股票名称解析
  - `market_status` — 市场状态查询
- `pyproject.toml`：注册 `dsa` 命令行入口

#### 4.2 Fork 版权声明
- LICENSE 追加 Copyright (c) 2026 kuaizhongqiang
- 保留原始版权 Copyright (c) 2026 ZhuLinsen

### 5. 未改动（保留的核心能力）

- 核心分析引擎：`src/core/pipeline.py`
- 多 Agent 系统：`src/agent/`（orchestrator, executor, agents, skills, tools）
- 多源数据抓取：`data_provider/`（efinance, akshare, tushare, yfinance 等）
- FastAPI REST API：`api/`、`server.py`
- 策略系统：`strategies/`（15+ YAML 策略）
- 业务服务：`src/services/`（analyzer, analysis, alert, portfolio, backtest）
- 数据库访问：`src/repositories/`
- 数据 Schema：`src/schemas/`
- 搜索引擎集成：Bocha、Tavily、SerpAPI、Brave、SearXNG

---

## 技术栈

| 组件 | 原项目 | Fork |
|------|--------|------|
| LLM | 云 API（Gemini/DeepSeek/OpenAI 等） | 本地 LM Studio（可切换） |
| 触发方式 | cron 定时 + Web UI | AI Agent 按需（CLI/MCP/API） |
| 输出 | 报告 + 多渠道推送 | JSON（Agent 消费） |
| CLI | 无 | `dsa` CLI + MCP Server |
| Web UI | React + Vite + Tailwind | 已移除 |
| 桌面端 | Electron | 已移除 |
| Bot | 钉钉/飞书/Discord | 已移除 |

---

## 文件结构变化

```
原项目                        Fork
─────                        ────
apps/dsa-web/    →  [删除] Web UI
apps/dsa-desktop/ → [删除] 桌面端
bot/              →  [删除] Bot 渠道
templates/        →  [删除] Jinja2 报告模板
src/notification* →  [删除] 通知模块
src/md2img.py     →  [删除] Markdown 转图片
src/webui_frontend.py → [删除]
webui.py           →  [删除]
.github/release.yml → [删除]
自动工作流 3 个   →  [删除]
docs/ 约 100 文件  →  精简至 3 个
                              ↓
dsa/               →  [新增] CLI + MCP Server
docs/CHANGELOG.md  →  [保留]
docs/architecture/api_spec.json → [保留]
docs/openclaw-skill-integration.md → [保留+更新]
```

---

## 兼容性说明

- REST API 端点保持不变（`/api/v1/analysis/analyze` 等）
- 配置方式保持 `.env` 文件格式
- 策略 YAML 格式不变
- 数据库 Schema 不变
- 默认 LLM 改为 LM Studio（原为 Gemini）
- 不再支持：Web UI、桌面端、Bot、通知推送、定时任务

---

## License

MIT License — 保留原始版权 (c) 2026 ZhuLinsen，追加 Fork 版权 (c) 2026 kuaizhongqiang。
