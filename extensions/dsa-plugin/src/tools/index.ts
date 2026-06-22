/**
 * DSA Plugin Tools 定义
 *
 * 将 DSA REST API 20+ 端点映射为 OpenClaw Plugin 原生 Tools。
 * 每个 Tool 包含：name, description, inputSchema (JSON Schema), handler
 */

import type { ToolDefinition, ToolContext } from '../types.js';
import type { DsaClient } from '../client.js';
import { DsaApiError } from '../client.js';
import type { SessionContextManager } from '../context.js';

// ============================================================
// 辅助：从上下文中提取 DSA 客户端
// ============================================================

function getClient(ctx: ToolContext): DsaClient {
  const client = (ctx as any).__dsaClient as DsaClient;
  if (!client) {
    throw new Error('DSA 客户端未初始化');
  }
  return client;
}

function getSessionManager(ctx: ToolContext): SessionContextManager {
  const mgr = (ctx as any).__sessionManager as SessionContextManager;
  if (!mgr) {
    throw new Error('会话管理器未初始化');
  }
  return mgr;
}

// ============================================================
// Tool 定义
// ============================================================

/** 分析股票 */
export const analyzeStockTool: ToolDefinition = {
  name: 'analyze_stock',
  description: '对单只股票执行全量分析（技术面 + 新闻搜索 + LLM 分析），返回包含操作建议、趋势预测、策略价位的完整报告。分析约需 2-5 分钟。',
  inputSchema: {
    type: 'object',
    properties: {
      stock_code: {
        type: 'string',
        description: '股票代码。A股: 6位数字(600519); 港股: hk+5位(hk00700); 美股: AAPL/TSLA。不支持中文名称。',
      },
      report_type: {
        type: 'string',
        enum: ['simple', 'detailed', 'brief'],
        default: 'detailed',
        description: '报告详细程度',
      },
      force_refresh: {
        type: 'boolean',
        default: false,
        description: '是否强制刷新缓存',
      },
      skills: {
        type: 'array',
        items: { type: 'string' },
        description: '可选策略 ID 列表，如 ["bull_trend", "ma_golden_cross"]',
      },
    },
    required: ['stock_code'],
  },
  handler: async (input, ctx) => {
    const client = getClient(ctx);
    const sm = getSessionManager(ctx);
    const code = input.stock_code as string;

    // 记录会话上下文
    sm.setCurrentStock(ctx.sessionId, code, '');

    const result = await client.analyzeStock(code, {
      reportType: (input.report_type as string) ?? 'detailed',
      forceRefresh: (input.force_refresh as boolean) ?? false,
      skills: input.skills as string[] | undefined,
    });

    // 绑定分析结果到会话
    sm.setAnalysisResult(ctx.sessionId, code, {
      stockCode: result.stock_code,
      stockName: result.stock_name,
      sentimentScore: result.report.summary.sentiment_score,
      action: result.report.summary.action,
      actionLabel: result.report.summary.action_label,
      summary: result.report.summary.analysis_summary,
      timestamp: result.created_at,
    });

    return result;
  },
};

/** 实时行情 */
export const getStockQuoteTool: ToolDefinition = {
  name: 'get_stock_quote',
  description: '获取股票实时行情，包括最新价、涨跌幅、成交量、最高/最低价等。',
  inputSchema: {
    type: 'object',
    properties: {
      stock_code: {
        type: 'string',
        description: '股票代码，同 analyze_stock 格式',
      },
    },
    required: ['stock_code'],
  },
  handler: async (input, ctx) => {
    const client = getClient(ctx);
    return client.getStockQuote(input.stock_code as string);
  },
};

/** 解析股票 */
export const resolveStockTool: ToolDefinition = {
  name: 'resolve_stock',
  description: '解析股票代码或名称，返回标准化的股票代码、名称和市场信息。',
  inputSchema: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: '股票代码或简称，如 "600519"、"茅台"、"AAPL"',
      },
    },
    required: ['query'],
  },
  handler: async (input, ctx) => {
    const client = getClient(ctx);
    return client.resolveStock(input.query as string);
  },
};

/** 大盘行情 */
export const marketStatusTool: ToolDefinition = {
  name: 'market_status',
  description: '获取大盘行情概要，包括主要指数涨跌、领涨/领跌板块。',
  inputSchema: {
    type: 'object',
    properties: {},
  },
  handler: async (_input, ctx) => {
    const client = getClient(ctx);
    return client.getMarketStatus();
  },
};

/** 大盘复盘 */
export const runMarketReviewTool: ToolDefinition = {
  name: 'run_market_review',
  description: '执行大盘综合复盘，返回 LLM 生成的市场分析报告、板块轮动分析和后市展望。分析需 1-3 分钟。',
  inputSchema: {
    type: 'object',
    properties: {},
  },
  handler: async (_input, ctx) => {
    const client = getClient(ctx);
    return client.runMarketReview();
  },
};

/** 同步分析 */
export const runAnalysisSyncTool: ToolDefinition = {
  name: 'run_analysis_sync',
  description: '对单只股票执行分析并同步等待结果。与 analyze_stock 功能相同，但明确使用同步模式。',
  inputSchema: {
    type: 'object',
    properties: {
      stock_code: {
        type: 'string',
        description: '股票代码',
      },
      report_type: {
        type: 'string',
        enum: ['simple', 'detailed', 'brief'],
        default: 'detailed',
      },
      force_refresh: {
        type: 'boolean',
        default: false,
      },
    },
    required: ['stock_code'],
  },
  handler: async (input, ctx) => {
    const client = getClient(ctx);
    const sm = getSessionManager(ctx);
    const code = input.stock_code as string;

    sm.setCurrentStock(ctx.sessionId, code, '');
    const result = await client.analyzeStock(code, {
      reportType: (input.report_type as string) ?? 'detailed',
      forceRefresh: (input.force_refresh as boolean) ?? false,
    });

    sm.setAnalysisResult(ctx.sessionId, code, {
      stockCode: result.stock_code,
      stockName: result.stock_name,
      sentimentScore: result.report.summary.sentiment_score,
      action: result.report.summary.action,
      actionLabel: result.report.summary.action_label,
      summary: result.report.summary.analysis_summary,
      timestamp: result.created_at,
    });

    return result;
  },
};

/** 查询任务状态 */
export const checkJobStatusTool: ToolDefinition = {
  name: 'check_job_status',
  description: '查询异步分析任务的执行状态。用于 analyze_stock 异步模式后的轮询。',
  inputSchema: {
    type: 'object',
    properties: {
      task_id: {
        type: 'string',
        description: '异步任务 ID（analyze_stock 异步模式返回的 task_id）',
      },
    },
    required: ['task_id'],
  },
  handler: async (input, ctx) => {
    const client = getClient(ctx);
    return client.checkJobStatus(input.task_id as string);
  },
};

/** 语义搜索 */
export const semanticSearchTool: ToolDefinition = {
  name: 'semantic_search',
  description: '通过自然语言语义搜索股票信息。支持中文查询，如 "白酒龙头"、"最近强势的科技股"、"新能源板块"。',
  inputSchema: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: '自然语言查询语句',
      },
      limit: {
        type: 'number',
        default: 10,
        description: '返回结果数量上限',
      },
    },
    required: ['query'],
  },
  handler: async (input, ctx) => {
    const client = getClient(ctx);
    return client.semanticSearch(
      input.query as string,
      input.limit as number | undefined,
    );
  },
};

/** 向量索引状态 */
export const vectorIndexStatusTool: ToolDefinition = {
  name: 'vector_index_status',
  description: '查询语义搜索的向量索引状态，包括索引文档数量和运行状态。',
  inputSchema: {
    type: 'object',
    properties: {},
  },
  handler: async (_input, ctx) => {
    const client = getClient(ctx);
    return client.getVectorIndexStatus();
  },
};

/** 股池列表 */
export const poolListTool: ToolDefinition = {
  name: 'pool_list',
  description: '列出所有已创建的股池及基本信息。',
  inputSchema: {
    type: 'object',
    properties: {},
  },
  handler: async (_input, ctx) => {
    const client = getClient(ctx);
    return client.listPools();
  },
};

/** 创建股池 */
export const poolCreateTool: ToolDefinition = {
  name: 'pool_create',
  description: '创建新的股池，用于归类跟踪股票。',
  inputSchema: {
    type: 'object',
    properties: {
      name: {
        type: 'string',
        description: '股池名称，如 "强势股跟踪"、"茅台对标观察"',
      },
      description: {
        type: 'string',
        description: '股池描述（可选）',
      },
    },
    required: ['name'],
  },
  handler: async (input, ctx) => {
    const client = getClient(ctx);
    const sm = getSessionManager(ctx);
    const result = await client.createPool(
      input.name as string,
      input.description as string | undefined,
    );
    sm.addPoolRef(ctx.sessionId, result.id, result.name);
    return result;
  },
};

/** 股池详情 */
export const poolGetTool: ToolDefinition = {
  name: 'pool_get',
  description: '获取指定股池的详细信息和包含的股票列表。',
  inputSchema: {
    type: 'object',
    properties: {
      pool_id: {
        type: 'string',
        description: '股池 ID',
      },
    },
    required: ['pool_id'],
  },
  handler: async (input, ctx) => {
    const client = getClient(ctx);
    return client.getPool(input.pool_id as string);
  },
};

/** 添加股票到股池 */
export const poolAddStockTool: ToolDefinition = {
  name: 'pool_add_stock',
  description: '向指定股池添加一只股票。需要审批确认。',
  inputSchema: {
    type: 'object',
    properties: {
      pool_id: {
        type: 'string',
        description: '股池 ID',
      },
      stock_code: {
        type: 'string',
        description: '股票代码',
      },
    },
    required: ['pool_id', 'stock_code'],
  },
  handler: async (input, ctx) => {
    const client = getClient(ctx);
    return client.addStockToPool(
      input.pool_id as string,
      input.stock_code as string,
    );
  },
};

/** 从股池移除股票 */
export const poolRemoveStockTool: ToolDefinition = {
  name: 'pool_remove_stock',
  description: '从指定股池移除一只股票。需要审批确认。',
  inputSchema: {
    type: 'object',
    properties: {
      pool_id: {
        type: 'string',
        description: '股池 ID',
      },
      stock_code: {
        type: 'string',
        description: '股票代码',
      },
    },
    required: ['pool_id', 'stock_code'],
  },
  handler: async (input, ctx) => {
    const client = getClient(ctx);
    return client.removeStockFromPool(
      input.pool_id as string,
      input.stock_code as string,
    );
  },
};

/** 删除股池 */
export const poolDeleteTool: ToolDefinition = {
  name: 'pool_delete',
  description: '删除整个股池及其包含的所有股票关系。高危操作，需要审批确认。',
  inputSchema: {
    type: 'object',
    properties: {
      pool_id: {
        type: 'string',
        description: '股池 ID',
      },
    },
    required: ['pool_id'],
  },
  handler: async (input, ctx) => {
    const client = getClient(ctx);
    return client.deletePool(input.pool_id as string);
  },
};

/** 历史搜索 */
export const historySearchTool: ToolDefinition = {
  name: 'history_search',
  description: '搜索历史分析记录，按关键词匹配。',
  inputSchema: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: '搜索关键词，如 "茅台"、"600519"',
      },
      limit: {
        type: 'number',
        default: 20,
        description: '返回记录数量上限',
      },
    },
    required: ['query'],
  },
  handler: async (input, ctx) => {
    const client = getClient(ctx);
    return client.searchHistory(
      input.query as string,
      input.limit as number | undefined,
    );
  },
};

/** 历史统计 */
export const historyStatsTool: ToolDefinition = {
  name: 'history_stats',
  description: '获取历史分析的统计汇总：总分析次数、覆盖股票数、操作建议分布等。',
  inputSchema: {
    type: 'object',
    properties: {},
  },
  handler: async (_input, ctx) => {
    const client = getClient(ctx);
    return client.getHistoryStats();
  },
};

/** 历史导出 */
export const historyExportTool: ToolDefinition = {
  name: 'history_export',
  description: '导出历史分析记录。',
  inputSchema: {
    type: 'object',
    properties: {
      format: {
        type: 'string',
        enum: ['json', 'csv'],
        default: 'json',
        description: '导出格式',
      },
    },
  },
  handler: async (input, ctx) => {
    const client = getClient(ctx);
    return client.exportHistory(input.format as string | undefined);
  },
};

/** 清理旧历史 */
export const historyPruneTool: ToolDefinition = {
  name: 'history_prune',
  description: '清理指定天数之前的旧分析历史。高危操作，需要审批确认。',
  inputSchema: {
    type: 'object',
    properties: {
      older_than_days: {
        type: 'number',
        default: 90,
        description: '保留最近 N 天，N 天之前的将被删除',
      },
    },
  },
  handler: async (input, ctx) => {
    const client = getClient(ctx);
    return client.pruneHistory((input.older_than_days as number) ?? 90);
  },
};

/** Agent 策略问股 */
export const agentChatTool: ToolDefinition = {
  name: 'agent_chat',
  description: '通过 Agent 策略问股进行高级分析，支持缠论、均线金叉、波浪理论等多策略。需要 DSA 开启 AGENT_MODE=true。',
  inputSchema: {
    type: 'object',
    properties: {
      message: {
        type: 'string',
        description: '分析问题，如 "用缠论分析 600519"、"当前哪些板块有金叉信号"',
      },
      session_id: {
        type: 'string',
        description: '会话 ID（可选），用于多轮对话保持上下文',
      },
    },
    required: ['message'],
  },
  handler: async (input, ctx) => {
    const client = getClient(ctx);
    return client.agentChat(
      input.message as string,
      input.session_id as string | undefined,
    );
  },
};

/** 批量行情查询 */
export const getStockBatchTool: ToolDefinition = {
  name: 'get_stock_batch',
  description: '批量查询多只股票的实时行情。',
  inputSchema: {
    type: 'object',
    properties: {
      codes: {
        type: 'array',
        items: { type: 'string' },
        description: '股票代码数组，如 ["600519","000001","AAPL"]',
      },
    },
    required: ['codes'],
  },
  handler: async (input, ctx) => {
    const client = getClient(ctx);
    return client.getStockBatch(input.codes as string[]);
  },
};

// ============================================================
// 全部 Tool 列表
// ============================================================

export const allTools: ToolDefinition[] = [
  // 分析
  analyzeStockTool,
  runAnalysisSyncTool,
  checkJobStatusTool,

  // 行情
  getStockQuoteTool,
  getStockBatchTool,
  resolveStockTool,

  // 大盘
  marketStatusTool,
  runMarketReviewTool,

  // 股池
  poolListTool,
  poolCreateTool,
  poolGetTool,
  poolAddStockTool,
  poolRemoveStockTool,
  poolDeleteTool,

  // 搜索
  semanticSearchTool,
  vectorIndexStatusTool,

  // 历史
  historySearchTool,
  historyStatsTool,
  historyExportTool,
  historyPruneTool,

  // Agent
  agentChatTool,
];

/** 需要审批的高危 Tool 列表 */
export const highRiskTools = new Set<string>([
  'pool_add_stock',
  'pool_remove_stock',
  'pool_delete',
  'history_prune',
]);
