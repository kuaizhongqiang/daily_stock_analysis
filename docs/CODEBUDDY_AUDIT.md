# CodeBuddy 审查报告

**日期**: 2026-06-17
**审查人**: CodeBuddy
**范围**: 第一阶段 Fork 清理 + Claude coding 审查 + 第二阶段数据智能增强审查 + Issue 全局追踪

---

## 审查结论速览

| 阶段 | 新建 Issue | 阻断级 | 可关闭建议 |
|------|-----------|--------|-----------|
| 第一阶段 | 12 个（#22–#33, #40） | 3 | #1, #2, #3 |
| 第二阶段 | 13 个（#43–#55） | 5 | — |
| **合计** | **25 个** | **8** | **3**

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
| #5 | 接入本地 LLM（LM Studio） | 🔧 配置已就绪，适配器代码待实现 |
| #6 | 构建 dsa CLI | ✅ 框架已合并 main（#20） |
| #7 | 异步任务系统 | ✅ 基础实现已合并 main（#20） |
| #8 | dsa config | ✅ 已合并 main（#20） |
| #9 | dsa resolve | ✅ 已合并 main（#20） |
| #10 | 分析策略 CLI | ✅ 已合并 main（#20） |
| #11 | 批量编排 + Session | ⏳ 未开始 |
| #12 | 数据源自省 | ⚠️ sources.py 部分为桩，已合并 |
| #13 | dsa market | ✅ 已合并 main（#20） |
| #14 | dsa history / signals | ⚠️ history.py 有 bug（#29），已合并 |
| #15 | dsa alert | ⏳ 未开始 |
| #16 | 例行工作流模板 | ⏳ 未开始 |

### Fork 平台清理（#17–#21, #33）

| # | 标题 | 状态 |
|---|------|------|
| #17 | 移除平台自主行为 | ✅ 已合并 main |
| #18 | 精简 CI 工作流 | ✅ 已合并 main |
| #19 | LM Studio 默认配置 | ✅ 已合并 main |
| #20 | MCP 服务器 + CLI | ✅ 已合并 main, history.py bug 待修(#29) |
| #21 | OpenClaw 文档更新 | ⚠️ 已合并但 SKILL.md 未更新(#28) |
| #33 | 版权 + 残留清理 | ✅ 已合并 main

### CodeBuddy 新增（#22–#32, #40）

| # | 类别 | 标题 | 严重度 |
|---|------|------|--------|
| #22 | Security | Tushare API token HTTP 明文 | ✅ 已修复（commit 461265dd） |
| #23 | Security | SearXNG 公共实例默认启用 | ✅ 已修复（commit 461265dd） |
| #24 | Security | check_env.py 泄露 API Key 前缀 | Low |
| #25 | Chore | Fork 残留清理不全 | Low |
| #26 | Refactor | 核心模块超 2000 行 | Low |
| #27 | Block | pyproject.toml 缺少 [project] 段 | ✅ 已修复（#20 已合并） |
| #28 | Block | SKILL.md 描述与 MCP 路径不符 | 未修复 |
| #29 | Bug | dsa history.py `...` 占位符 | 未修复 |
| #30 | Gap | MCP 工具数 4 << CLI 命令 12+ | ✅ 已修复（commit 461265dd） |
| #31 | Gap | 缺少 MCP 协议合规性测试 | Medium |
| #32 | Refactor | CLI/MCP/API 错误格式不统一 | Medium |
| #40 | Chore | AGENTS.md 引用已删除路径 | Low |

---

## 安全发现

| 文件 | 问题 | Issue |
|------|------|-------|
| `data_provider/tushare_fetcher.py:78` | Token 通过 HTTP 明文传输 | #22 ✅ 已修复 |
| `.env.example:320` | SearXNG 公共实例默认 `true` | #23 ✅ 已修复 |
| `scripts/check_env.py:103-108` | 打印 API Key 前 8 位字符 | #24 ⚠️ 未修复 |
| `api/v1/endpoints/vector_search.py` | HTTP 响应泄露原始异常 | #50 🆕 P2 |
| `.env.example` | 11 个新配置项未同步 | #51 🆕 P2 |

---

## 已合并分支（第一阶段）

| 合并 | 包含 Issue | 状态 |
|------|-----------|------|
| `770137ae` Fork 清理合并 | #17, #18, #19, #20, #33 | ✅ 已合并 main |
| 各独立 commit | #1, #2, #3, #4, #5 | ✅ 已合并 main

---

## 未覆盖的风险面（第一阶段）

1. MCP Server 未与真实客户端（Claude Desktop）做互操作测试 (#31)
2. SKILL.md 与实际调用路径不一致，Agent 可能调用失败 (#28)
3. dsa history.py `...` 占位符运行时 bug (#29)
4. CLI/MCP/API 三层错误格式互不兼容 (#32)
5. check_env.py 打印 API Key 前 8 位字符 (#24)
6. AGENTS.md 引用已删除 Web/Desktop/Schedule 路径 (#40)

---

## 第二阶段审计：数据智能增强

**审查范围**: Sprint 1（股池基础设施）+ Sprint 2（向量搜索）+ Sprint 3（历史消息留存）
**新增文件**: 17 个 | **修改文件**: 9 个 | **新增模型**: 6 个 | **状态**: 未 commit（所有改动在 working tree）

### Issue 矩阵（#43–#55）

| # | 类别 | 标题 | 严重度 |
|---|------|------|--------|
| #43 | Block | Pipeline session 创建用裸 except:pass | 阻断 |
| #44 | Block | delete_document 重嵌全部剩余文档 | 阻断 |
| #45 | Block | EmbeddingService remote/local 相同默认 URL | 阻断 |
| #46 | Block | metadata.json 无并发保护 | 阻断 |
| #47 | Block | 向量搜索 dot product 未做 L2 归一化 | 阻断 |
| #48 | Bug | VectorIndexRepository 是死代码 | Medium |
| #49 | Bug | DataExportService 是纯委托 wrapper | Low |
| #50 | Security | vector_search API 泄露原始异常 | Medium |
| #51 | Security | 11 个新配置项未同步 .env.example | Medium |
| #52 | Gap | 17 个新文件零测试覆盖 | High |
| #53 | Gap | Pipeline 未自动触发向量索引 | High |
| #54 | Gap | DataQualityLog 从未被写入 | Medium |
| #55 | Quality | N+1 查询 + 全量加载 + 全排序 | Medium |

### 向量搜索设计审查

| 方面 | 设计 | 实现 | 问题 |
|------|------|------|------|
| Embedding 提供者 | LM Studio /v1/embeddings API | ✅ 正确 | — |
| 零 Python 模型依赖 | 无 sentence-transformers | ✅ 正确 | — |
| local/remote 双模式 | EMBEDDING_PROVIDER 切换 | ⚠️ 实现 | remote 默认 URL 与 local 相同 (#45) |
| 分块策略 | 512 char, 64 overlap | ✅ 正确 | — |
| 相似度算法 | 余弦相似度 | ⚠️ 有误 | 未做 L2 归一化 (#47) |
| 元数据存储 | JSON 文件 | ⚠️ 有风险 | 无并发保护 (#46), SQLite repo 未使用 (#48) |
| 删除操作 | 重嵌全部 | ❌ 设计缺陷 | 删除 1 条 = 重建全部 (#44) |

### 新增模块审查摘要

| 模块 | 评估 | 关键问题 |
|------|------|---------|
| `embedding_service.py` | ⚠️ 基本正确 | remote 模式默认 URL 错误 (#45) |
| `vector_search_service.py` | ❌ 3 阻断 | 归一化 (#47)、并发 (#46)、删除性能 (#44) |
| `stock_pool_service.py` | ✅ 基本正确 | N+1 查询 (#55) |
| `history_retention_service.py` | ✅ 基本正确 | LIKE 通配符 (#S3) |
| `data_quality_service.py` | ⚠️ 孤立模块 | 无人调用 (#54) |
| `data_export_service.py` | ⚠️ 多余 | 纯委托 wrapper (#49) |
| `stock_metadata_service.py` | ✅ 正确 | — |
| `data_import_service.py` | ✅ 基本正确 | 无编码处理 |
| `pool_tools.py` (Agent) | ✅ 正确 | — |
| `pool.py` (CLI) | ✅ 正确 | — |
| `vector.py` (CLI) | ✅ 正确 | — |
| `pools.py` (API) | ✅ 基本正确 | 每请求建 Service 实例 |
| `vector_search.py` (API) | ⚠️ | 异常泄露 (#50) |

### 数据模型审查

| 模型 | 评估 |
|------|------|
| StockPool | ✅ 字段完整 |
| StockPoolMember | ✅ 多对多关联正确 |
| StockMetadata | ✅ 元数据字段合理 |
| DataQualityLog | ⚠️ 无人写入 (#54) |
| AnalysisSession | ⚠️ exported_at/retention_days 未使用 |
| VectorIndexEntry | ⚠️ 死代码，VectorSearchService 未使用 (#48) |

### 代码状态

- **分支**: `feat/phase2-data-enhancement`
- **commit**: `aee0f4b4` feat: 第二阶段数据智能增强
- **文件变更**: 31 files, +3499/-68
- **pytest**: 待执行

### 第二轮审查结果（2026-06-17）

| Issue | 标题 | 第一轮 | 第二轮 |
|-------|------|--------|--------|
| #43 | Pipeline session except:pass | Block | ✅ FIXED |
| #44 | delete_document 重嵌全部 | Block | ❌ NOT FIXED |
| #45 | EmbeddingService remote/local URL | Block | ⚠️ PARTIAL |
| #46 | metadata.json 并发保护 | Block | ✅ FIXED |
| #47 | 向量未 L2 归一化 | Block | ✅ FIXED |
| #51 | .env.example 未更新 | Security | ✅ FIXED |
| #52 | 新文件零测试覆盖 | Gap | ⚠️ PARTIAL |
| #57 | DataQualityService except:pass | NEW | Block |
