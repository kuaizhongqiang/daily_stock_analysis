/**
 * 审批流接入
 *
 * 将高危操作（批量操作、股池删除、历史清理等）接入 OpenClaw 审批引擎。
 * 用户确认后才执行，防止误操作。
 */

import type { PluginContext, ApprovalResult } from './types.js';
import type { ToolContext } from './types.js';
import { DsaApiError } from './client.js';
import { highRiskTools } from './tools/index.js';

// ============================================================
// 审批辅助
// ============================================================

/** 判断操作是否需要审批 */
export function isHighRisk(toolName: string): boolean {
  return highRiskTools.has(toolName);
}

/** 构建审批卡片内容 */
export function buildApprovalBody(
  toolName: string,
  input: Record<string, unknown>,
): { title: string; body: string; severity: 'info' | 'warning' | 'critical' } {
  switch (toolName) {
    case 'pool_delete': {
      return {
        title: '⚠️ 确认删除股池',
        body: [
          `**操作**: 删除股池 \`${input.pool_id}\``,
          '',
          '**影响**:',
          '- 股池将从列表中移除',
          '- 股池与股票的关联关系将被删除',
          '- 股池内的股票不会被删除，仅解除关联',
          '',
          '**建议**: 确认该股池已不再需要。',
        ].join('\n'),
        severity: 'warning',
      };
    }

    case 'pool_add_stock': {
      return {
        title: '📋 确认添加股票到股池',
        body: [
          `**操作**: 将 \`${input.stock_code}\` 添加到股池 \`${input.pool_id}\``,
          '',
          '**影响**:',
          '- 该股票将被纳入股池跟踪',
          '- 后续轮询将覆盖此股票',
          '',
        ].join('\n'),
        severity: 'info',
      };
    }

    case 'pool_remove_stock': {
      return {
        title: '⚠️ 确认从股池移除股票',
        body: [
          `**操作**: 从股池 \`${input.pool_id}\` 中移除 \`${input.stock_code}\``,
          '',
          '**影响**:',
          '- 该股票将从股池跟踪列表中移除',
          '- 不会删除分析历史记录',
          '',
        ].join('\n'),
        severity: 'warning',
      };
    }

    case 'history_prune': {
      return {
        title: '🚨 确认清理历史数据',
        body: [
          `**操作**: 清理 ${input.older_than_days ?? 90} 天前的分析历史`,
          '',
          '**影响**:',
          '- 将删除符合条件的旧分析记录',
          '- **此操作不可撤销**',
          '',
          `**保留**: 最近 ${input.older_than_days ?? 90} 天的记录不受影响`,
        ].join('\n'),
        severity: 'critical',
      };
    }

    default: {
      return {
        title: `确认执行: ${toolName}`,
        body: `**操作**: \`${toolName}\`\n\n**参数**:\n\`\`\`json\n${JSON.stringify(input, null, 2)}\n\`\`\``,
        severity: 'warning',
      };
    }
  }
}

// ============================================================
// 审批包装器
// ============================================================

/**
 * 包装 Tool handler，自动判断是否需要审批。
 * 如果 Tool 在高危名单中，先发起审批，通过后才执行实际 handler。
 */
export function withApproval(
  toolName: string,
  handler: (input: Record<string, unknown>, ctx: ToolContext) => Promise<unknown>,
): (input: Record<string, unknown>, ctx: ToolContext) => Promise<unknown> {
  return async (input, ctx) => {
    // 不在高危名单中，直接执行
    if (!isHighRisk(toolName)) {
      return handler(input, ctx);
    }

    // 需要审批 — 通过插件上下文的 approval runtime
    const pluginCtx = (ctx as any).__pluginContext as PluginContext | undefined;
    const approval = pluginCtx?.approval;

    if (!approval) {
      // 没有审批运行时，降级为直接执行（静默降级，v0.1 兼容）
      pluginCtx?.log.warn(
        `[dsa-plugin] 高危操作 "${toolName}" 无审批运行时，直接执行`,
      );
      return handler(input, ctx);
    }

    const { title, body, severity } = buildApprovalBody(toolName, input);

    let result: ApprovalResult;
    try {
      result = await approval.request({
        title,
        body,
        severity,
        timeoutMs: 60_000, // 1 分钟超时
        actionId: `${toolName}_${Date.now()}`,
      });
    } catch (err) {
      throw new DsaApiError(
        403,
        'approval_error',
        `审批流程异常: ${(err as Error).message}`,
      );
    }

    switch (result.verdict) {
      case 'approved':
        return handler(input, ctx);
      case 'rejected':
        throw new DsaApiError(
          403,
          'operation_rejected',
          `操作已被拒绝: ${result.reason ?? '用户未批准'}`,
        );
      case 'timeout':
        throw new DsaApiError(
          403,
          'approval_timeout',
          '审批超时，操作已自动取消。如需执行，请重新发起。',
        );
    }
  };
}
