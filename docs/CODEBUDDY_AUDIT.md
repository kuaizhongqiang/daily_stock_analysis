# CodeBuddy 审查报告

**日期**: 2026-06-17
**审查人**: CodeBuddy
**范围**: 全仓库审查 + Claude coding 产出审查 + Issue 状态审查

---

## 审查结论速览

- **新建 Issue**: 12 个（#22–#33, #40）
- **建议关闭**: #1, #2, #3（已验证完成）
- **待合并分支**: 6 个（#17, #18, #19, #20, #21, #33）
- **安全风险**: 3 个 Medium（#22, #23, #24）
- **架构缺陷**: 3 个（#30, #31, #32）

---

## Issue 状态矩阵

### Fork 清理（#1–#4）

| # | 标题 | 状态 |
|---|------|------|
| #1 | 砍掉 Bot 渠道 + 通知模块 | ✅ 完成，建议关闭 |
| #2 | 摘除 pushplus 模块 | ✅ 完成，建议关闭 |
| #3 | 清理 Web UI 前端代码 | ✅ 完成，建议关闭 |
| #4 | 清理可视化 + 推送残留 | ⚠️ 部分完成，残余项 → #25 |

### Agent 改造（#5–#16）

| # | 标题 | 状态 |
|---|------|------|
| #5 | 接入本地 LLM（LM Studio） | 🔧 配置已就绪（#19 分支），适配器代码待实现 |
| #6 | 构建 dsa CLI | 🔧 框架已就绪（#20 分支），待合并 |
| #7 | 异步任务系统 | 🔧 基础实现（#20 分支） |
| #8 | dsa config | 🔧 基础实现（#20 分支） |
| #9 | dsa resolve | 🔧 已实现（#20 分支） |
| #10 | 分析策略 CLI | 🔧 部分实现（#20 分支） |
| #11 | 批量编排 + Session | ⏳ 未开始 |
| #12 | 数据源自省 | ⚠️ 部分为桩（#20 分支 sources.py） |
| #13 | dsa market | 🔧 已实现（#20 分支） |
| #14 | dsa history / signals | ⚠️ history.py 有 bug（#29） |
| #15 | dsa alert | ⏳ 未开始 |
| #16 | 例行工作流模板 | ⏳ 未开始 |

### Fork 平台清理（#17–#21, #33）

| # | 标题 | 分支 | 状态 |
|---|------|------|------|
| #17 | 移除平台自主行为 | `fix/issue-17-remove-autonomy` | ✅ 代码正确，待合并 |
| #18 | 精简 CI 工作流 | `chore/issue-18-ci-cleanup` | ⚠️ 仅改 Dockerfile |
| #19 | LM Studio 默认配置 | `config/issue-19-lm-studio-default` | ✅ 代码正确，待合并 |
| #20 | MCP 服务器 + CLI | `feat/issue-20-mcp-server` | ⚠️ history.py bug（#29） |
| #21 | OpenClaw 文档更新 | `docs/issue-21-openclaw` (HEAD) | ⚠️ 不完整 |
| #33 | 版权 + 残留清理 | `chore/issue-33-copyright-cleanup` | ⚠️ 删了改动清单.md |

### CodeBuddy 新增（#22–#32, #40）

| # | 类别 | 标题 | 严重度 |
|---|------|------|--------|
| #22 | Security | Tushare API token HTTP 明文 | Medium |
| #23 | Security | SearXNG 公共实例默认启用 | Medium |
| #24 | Security | check_env.py 泄露 API Key 前缀 | Low |
| #25 | Chore | Fork 残留清理不全 | Low |
| #26 | Refactor | 核心模块超 2000 行 | Low |
| #27 | Block | pyproject.toml 缺少 [project] 段 | 已修复→#20 |
| #28 | Block | SKILL.md 描述与 MCP 路径不符 | 未修复 |
| #29 | Bug | dsa history.py `...` 占位符 | 未修复 |
| #30 | Gap | MCP 工具数 4 << CLI 命令 12+ | Medium |
| #31 | Gap | 缺少 MCP 协议合规性测试 | Medium |
| #32 | Refactor | CLI/MCP/API 错误格式不统一 | Medium |
| #40 | Chore | AGENTS.md 引用已删除路径 | Low |

---

## 安全发现

| 文件 | 问题 | Issue |
|------|------|-------|
| `data_provider/tushare_fetcher.py:78` | Token 通过 HTTP 明文传输 | #22 |
| `.env.example:320` | SearXNG 公共实例默认 `true` | #23 |
| `scripts/check_env.py:103-108` | 打印 API Key 前 8 位字符 | #24 |

---

## 未合并分支

| 分支 | Issue | 评价 |
|------|-------|------|
| `fix/issue-17-remove-autonomy` | #17 | ✅ 可合并 |
| `chore/issue-18-ci-cleanup` | #18 | ⚠️ 仅清理 Dockerfile |
| `config/issue-19-lm-studio-default` | #19 | ✅ 可合并 |
| `feat/issue-20-mcp-server` | #20 | ⚠️ 需先修 #29 |
| `docs/issue-21-openclaw` | #21 | ⚠️ 不完整 |
| `chore/issue-33-copyright-cleanup` | #33 | ⚠️ 改动清单.md 删除待确认 |

建议合并顺序: #17 → #33 → #19 → #18 → #20 → #21

---

## 未覆盖的风险面

1. MCP Server 未与真实客户端（Claude Desktop）做互操作测试
2. SKILL.md 与实际调用路径不一致，Agent 可能调用失败
3. dsa history.py 运行即崩溃
4. CLI/MCP/API 三层错误格式互不兼容，Agent 错误处理碎片化
5. MCP 工具不足（仅 4 个），CLI 半数能力对 Agent 不可见
