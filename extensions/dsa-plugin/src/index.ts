/**
 * DSA Plugin — OpenClaw Plugin 入口
 *
 * 将 daily_stock_analysis 分析引擎集成到 OpenClaw。
 *
 * ## 注册流程
 * 1. 初始化 DSA HTTP 客户端
 * 2. 注册 20+ 工具（行情、分析、股池、搜索、历史）
 * 3. 工具自动接入审批流（高危操作需确认）
 * 4. 启动主动推送轮询（股价预警）
 * 5. 会话上下文管理（追问、对比）
 */

import { definePlugin, type PluginContext } from './types.js';
import { DsaClient } from './client.js';
import { allTools, highRiskTools } from './tools/index.js';
import { withApproval } from './approval.js';
import { PushManager, type PushConfig } from './push.js';
import { sessionManager } from './context.js';
import type { ToolContext } from './types.js';

/** 从 Plugin 配置中读取 DSA 客户端配置 */
function resolveClientConfig(ctx: PluginContext) {
  const cfg = ctx.config;
  return {
    baseUrl: (cfg['dsa.baseUrl'] as string) || 'http://localhost:8000',
    requestTimeout: (cfg['dsa.requestTimeout'] as number) || 300_000,
  };
}

/** 从 Plugin 配置中读取推送配置 */
function resolvePushConfig(ctx: PluginContext): PushConfig {
  const cfg = ctx.config;
  return {
    pollInterval: (cfg['dsa.push.pollInterval'] as number) || 600_000,
    stopLossThreshold: (cfg['dsa.push.stopLossThreshold'] as number) || 0.95,
    takeProfitThreshold:
      (cfg['dsa.push.takeProfitThreshold'] as number) || 1.1,
  };
}

/**
 * OpenClaw Plugin 定义
 *
 * 通过 definePlugin 声明插件元数据和注册函数。
 * OpenClaw 加载时调用 register(context) 完成初始化。
 */
export default definePlugin({
  name: 'dsa-plugin',
  version: '0.1.0',
  description: '深度集成 daily_stock_analysis 分析引擎 — 行情、分析、股池、语义搜索全链路',

  register(context: PluginContext) {
    // ---- 1. 初始化 DSA 客户端 ----
    const dsaConfig = resolveClientConfig(context);
    const client = new DsaClient(dsaConfig);

    context.log.info(
      `[dsa-plugin] DSA 客户端已初始化 -> ${dsaConfig.baseUrl}`,
    );

    // ---- 2. 注册所有工具 ----
    // 将 DSA 客户端和会话管理器注入到 ToolContext 中
    const enhancedContext = context as PluginContext & {
      __dsaClient: DsaClient;
      __sessionManager: typeof sessionManager;
    };

    for (const tool of allTools) {
      const originalHandler = tool.handler;

      // 包装 handler: 注入客户端 + 会话管理器
      const wrappedHandler = async (
        input: Record<string, unknown>,
        toolCtx: ToolContext,
      ) => {
        // 注入依赖到 ToolContext
        (toolCtx as any).__dsaClient = client;
        (toolCtx as any).__sessionManager = sessionManager;
        (toolCtx as any).__pluginContext = context;

        // 应用审批流包装
        const approvedHandler = withApproval(tool.name, originalHandler);
        return approvedHandler(input, toolCtx);
      };

      context.registerTool({
        name: tool.name,
        description: tool.description,
        inputSchema: tool.inputSchema,
        handler: wrappedHandler,
      });

      context.log.info(`[dsa-plugin] 已注册工具: ${tool.name}`);
    }

    context.log.info(
      `[dsa-plugin] 共注册 ${allTools.length} 个工具，其中 ${highRiskTools.size} 个高危操作需审批`,
    );

    // ---- 3. 启动主动推送 ----
    const pushConfig = resolvePushConfig(context);
    const pushManager = new PushManager(client, pushConfig, context);
    pushManager.start();

    // ---- 4. 定期清理过期会话 ----
    setInterval(() => {
      const cleaned = sessionManager.cleanIdleSessions();
      if (cleaned > 0) {
        context.log.info(`[dsa-plugin] 已清理 ${cleaned} 个超时会话`);
      }
    }, 5 * 60 * 1000); // 每 5 分钟清理一次

    // ---- 5. 每天重置告警记录 ----
    const resetAt = new Date();
    resetAt.setHours(24, 0, 0, 0); // 次日 00:00
    const msUntilMidnight = resetAt.getTime() - Date.now();
    if (msUntilMidnight > 0) {
      setTimeout(() => {
        pushManager.resetDailyAlerts();
        context.log.info('[dsa-plugin] 已重置每日告警记录');
      }, msUntilMidnight);
    }

    context.log.info('[dsa-plugin] 注册完成，插件已就绪');
  },
});
