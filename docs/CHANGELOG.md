# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

> For user-friendly release highlights, see the [GitHub Releases](https://github.com/ZhuLinsen/daily_stock_analysis/releases) page.

## [Unreleased]

- [修复] 问股从历史报告进入后的追问会持续携带当前标的，切回或重载已有会话时可从历史消息恢复基础当前标的，并由后端阻断未明确切换时的错误股票工具调用、交易所片段和指标缩写误路由。
- [修复] 自选股加入和删除按等价股票代码匹配港股及大小写美股变体，避免 `00700`、`HK00700`、`00700.HK` 或 `aapl`、`AAPL` 被误判为不同标的。
- [改进] #1390 P0 为个股分析与历史/回测展示新增可选八态 `action` / `action_label` 建议动作字段，保留 `operation_advice` 自由文本和 `decision_type=buy|hold|sell` 统计口径，不新增迁移或配置项。
- [新功能] #1390 P1 新增独立 `DecisionSignal` 存储、Repository、Service 与 `/api/v1/decision-signals` API，支持按来源类型/市场/股票/动作/期限/阶段去重、按 `source_report_id` / `trace_id` 查询、同源过期信号续期且保留来源身份字段、禁止 expired 直接 PATCH 复活、价格计划校验、状态更新、懒过期、cache-only 持仓过滤、敏感信息脱敏、敏感 `trace_id` 拒绝和仅清理 `source_type=analysis` 历史绑定信号的历史删除联动。
- [改进] #1390 P1 补充 Web decision-signals typed API wrapper 与契约隔离测试，暂不接入 UI。
- [修复] #1390 收紧建议动作 legacy fallback：英文 `not to ...` 与 `avoid selling/reducing/trimming ...` 等否定/回避表达不再误判为买卖动作，Web 旧记录不再把中文金融上下文、`buy or sell`、多 guard 歧义文本或 `buyback` / `buy-back` / `buy back` / `selloff` / `sell-off` / `sell off` 等英文复合词渲染成 action badge，并在有结构化 `action` 时让回测/历史趋势等入口按界面语言显示 action 标签。
- [改进] 完善运行时日志上下文，补充 logger name、触发来源、市场统计与实时行情预取链路状态，便于排查调度、API、Bot 和数据源降级路径。
- [新功能] 新增分析任务与历史报告运行流快照 API，提供 lanes、nodes、edges、events、summary 等统一契约，并从任务队列、运行诊断和 AnalysisContextPack overview 构建脱敏数据流/信息流。
- [新功能] Web 端为活跃任务、历史报告和大盘复盘报告补充运行流视图入口，支持查看运行摘要、拓扑节点、事件流和基础排障详情。
- [修复] 修复历史报告运行流快照在混合时区事件时间戳下返回 500 的问题。
- [改进] #1459 持仓管理页新增持仓账户删除入口，复用现有账户软删除接口，误建账户会从默认列表、快照、风险、录入入口和事件列表隐藏且不物理清理历史流水。
<!-- 新条目格式：- [类型] 描述（类型取值：新功能/改进/修复/文档/测试/chore）-->
<!-- 每条独立一行追加到本段末尾，无需分类标题，合并时冲突最小 -->
- [修复] 桌面发布打包改用冻结可执行文件运行时探针校验 `alphasift.dsa_adapter`，避免 macOS PyInstaller 将模块内嵌进可执行文件时被文件系统/zip 扫描误判为缺失。
- [修复] #69 hot_topics schema 校验警告：LLM 返回列表时 Pydantic 校验失败，新增 field_validator 自动转换 list/dict 为字符串，同时 analyzer.py 添加兜底处理
- [新功能] #70 新增 `GET /api/v1/pools/overview` 股池总览接口（含行情+分析摘要+策略价位嵌套结构）
- [新功能] #70 新增 `GET /api/v1/stocks/batch` 批量精简行情接口（供插件轮询刷新）
- [修复] #71 `GET /api/v1/stocks/{code}/quote` 在所有股票返回 not_found：外部实时数据源不可用时新增数据库 `stock_daily` 最新日线降级兜底，下游 personal-helper-server 数据聚合不再为空
- [重构] 剥离 MCP Server 代码（`dsa/commands/mcp.py` + `dsa/mcp_server.py`），`dsa-server` 包统一为 CLI + API，入口：`dsa`（CLI）和 `dsa serve`（API）
- [重构] 删除 `dsa-server` 独立入口点，`server:main_cli` 整合为 `dsa serve` 子命令

<!-- 新条目格式：- [类型] 描述（类型取值：新功能/改进/修复/文档/测试/chore）-->
<!-- 每条独立一行追加到本段末尾，无需分类标题，合并时冲突最小 -->

## [0.1.5] - 2026-06-22

### Fork 修复（kuaizhongqiang fork）

- [修复] LLM 调用时报 `ascii codec cant encode character …`：`orchestrator.py` 中 `_truncate_text` 使用 `…` (U+2026) 改为 `...`（#68）

## [0.1.4] - 2026-06-22

### Fork 修复（kuaizhongqiang fork）

- [修复] `dsa analyze` 输出报告为空：CLI 代码错误使用 `r.score`/`r.summary` 属性名，应为 `sentiment_score`/`analysis_summary`（#68）
- [修复] `LLM_LM_STUDIO_BASE_URL` 环境变量未映射到 LiteLLM：当 `OPENAI_BASE_URL` 未设置时，自动 fallback 到 `LLM_LM_STUDIO_BASE_URL`（#68）
- [改进] `dsa analyze` 输出添加 `decision_type`、`confidence_level` 等字段

## [0.1.3] - 2026-06-22

### Fork 修复（kuaizhongqiang fork）
- [修复] `pip install dsa-server` 后 `dsa analyze` 报错：`strategies/` 目录未打包到 wheel 中（#67）
- [修复] `pip install dsa-server` 后 `dsa analyze` 报错：`StockAnalysisPipeline.run()` 被传入已移除的 `send_notification` 参数（#67）
- [修复] `pip install dsa-server` 后 `.env` 文件查找路径错误：pip 安装版从 `site-packages/.env` 查找而非 CWD（#67）
- [修复] `main.py` 中 `pipeline.run()` 调用传入了已移除的 `send_notification` 和 `merge_notification` 参数
- [chore] 添加 `MANIFEST.in` 确保数据文件正确打包
- [chore] LICENSE 更新：添加 fork 维护者版权信息
