/**
 * 主动推送 — 股价预警通知
 *
 * 基于 Plugin 定时能力，轮询股池行情，触发止盈/止损时主动推送到当前 Channel。
 *
 * 流程:
 *   定时器 → 读取所有股池 → 批量查询行情 → 比对策略价位 → 触发告警 → Channel 推送
 */

import type { PluginContext } from './types.js';
import type { DsaClient, StockQuote } from './client.js';

// ============================================================
// 类型定义
// ============================================================

export interface PushConfig {
  /** 轮询间隔（毫秒），默认 10 分钟 */
  pollInterval: number;
  /** 止损阈值，现价/参考价低于此值触发 */
  stopLossThreshold: number;
  /** 止盈阈值，现价/参考价高于此值触发 */
  takeProfitThreshold: number;
}

export interface AlertRecord {
  stockCode: string;
  stockName: string;
  alertType: 'stop_loss' | 'take_profit';
  currentPrice: number;
  referencePrice: number;
  triggeredAt: string;
}

export interface StrategyPrice {
  /** 理想买入价 */
  idealBuy: number;
  /** 止损价 */
  stopLoss: number;
  /** 止盈价 */
  takeProfit: number;
}

// ============================================================
// 推送管理器
// ============================================================

export class PushManager {
  private client: DsaClient;
  private config: PushConfig;
  private context: PluginContext;
  private timerId: ReturnType<typeof setInterval> | null = null;
  /** 已告警记录（同一天同一股票不重复告警） */
  private alertedToday = new Set<string>();

  constructor(
    client: DsaClient,
    config: PushConfig,
    context: PluginContext,
  ) {
    this.client = client;
    this.config = config;
    this.context = context;
  }

  /** 启动定时轮询 */
  start(): void {
    if (this.timerId) return;

    this.context.log.info(
      `[dsa-plugin] 主动推送已启动，轮询间隔 ${this.config.pollInterval / 1000}s`,
    );

    // 立即执行一次
    this.poll().catch((err) => {
      this.context.log.error('[dsa-plugin] 首次轮询失败:', err);
    });

    // 定时执行
    this.timerId = setInterval(() => {
      this.poll().catch((err) => {
        this.context.log.error('[dsa-plugin] 轮询失败:', err);
      });
    }, this.config.pollInterval);
  }

  /** 停止轮询 */
  stop(): void {
    if (this.timerId) {
      clearInterval(this.timerId);
      this.timerId = null;
    }
  }

  /** 执行一次轮询 */
  async poll(): Promise<void> {
    this.context.log.info('[dsa-plugin] 开始轮询股池行情...');

    let pools;
    try {
      pools = await this.client.listPools();
    } catch (err) {
      this.context.log.warn('[dsa-plugin] 获取股池列表失败，跳过本轮:', err);
      return;
    }

    if (!pools || pools.length === 0) {
      this.context.log.info('[dsa-plugin] 无股池，跳过本轮');
      return;
    }

    // 遍历每个股池，获取详情和行情
    for (const pool of pools) {
      try {
        await this.checkPool(pool.id, pool.name);
      } catch (err) {
        this.context.log.warn(
          `[dsa-plugin] 检查股池 "${pool.name}" 失败:`,
          err,
        );
      }
    }
  }

  /** 检查单个股池 */
  private async checkPool(poolId: string, poolName: string): Promise<void> {
    let detail;
    try {
      detail = await this.client.getPool(poolId);
    } catch {
      // DSA 的 getPool 可能不支持 stocks 字段，跳过
      return;
    }

    const stocks = (detail as any).stocks;
    if (!stocks || !Array.isArray(stocks) || stocks.length === 0) return;

    // 批量查询行情
    let quotes: StockQuote[];
    try {
      quotes = await this.client.getStockBatch(stocks);
    } catch {
      // 批量接口可能不支持，逐个查询
      return; // 跳过本轮
    }

    if (!quotes || quotes.length === 0) return;

    for (const quote of quotes) {
      // 检查是否已告警（同一天同一股票不重复）
      const alertKey = this.alertKey(quote.code);
      if (this.alertedToday.has(alertKey)) continue;

      // 从最近的分析结果获取策略价位
      // 注：v0.1 简化为基于最近一次分析的止盈止损价
      // 改进方向：从 DSA 获取该股票最近一次分析的 strategy 字段
      const alert = await this.evaluatePrice(quote);
      if (alert) {
        await this.sendAlert(alert, poolName);
        this.alertedToday.add(alertKey);
      }
    }
  }

  /** 评估价格是否触发告警 */
  private async evaluatePrice(
    quote: StockQuote,
  ): Promise<AlertRecord | null> {
    // 获取该股票最近的分析结果中的策略价位
    // v0.1 直接使用收盘价作为参考价，未来可从 DSA 分析结果中提取
    // TODO: 调用 DSA history API 获取最近一次分析的 strategy 数据
    const referencePrice = quote.prev_close || quote.price;

    if (referencePrice <= 0) return null;

    const changeRatio = (quote.price - referencePrice) / referencePrice;

    // 止损：现价比参考价跌幅超过阈值
    if (changeRatio <= -(1 - this.config.stopLossThreshold)) {
      return {
        stockCode: quote.code,
        stockName: quote.name,
        alertType: 'stop_loss',
        currentPrice: quote.price,
        referencePrice,
        triggeredAt: new Date().toISOString(),
      };
    }

    // 止盈：现价比参考价涨幅超过阈值
    if (changeRatio >= this.config.takeProfitThreshold - 1) {
      return {
        stockCode: quote.code,
        stockName: quote.name,
        alertType: 'take_profit',
        currentPrice: quote.price,
        referencePrice,
        triggeredAt: new Date().toISOString(),
      };
    }

    return null;
  }

  /** 推送告警消息 */
  private async sendAlert(alert: AlertRecord, poolName: string): Promise<void> {
    const label =
      alert.alertType === 'stop_loss' ? '🔴 止损预警' : '🟢 止盈提醒';
    const change = (
      ((alert.currentPrice - alert.referencePrice) / alert.referencePrice) *
      100
    ).toFixed(2);

    const body = [
      `**${alert.stockName} (${alert.stockCode})**`,
      `当前价: **${alert.currentPrice}**`,
      `参考价: ${alert.referencePrice}（${change >= '0' ? '+' : ''}${change}%）`,
      `来源股池: ${poolName}`,
      '',
      alert.alertType === 'stop_loss'
        ? `建议关注，考虑是否止损`
        : `已达到止盈目标位，建议关注`,
    ].join('\n');

    try {
      if (this.context.channel) {
        await this.context.channel.send({
          title: `${label}: ${alert.stockName}`,
          body,
          severity: alert.alertType === 'stop_loss' ? 'warning' : 'info',
          action: {
            type: 'analyze_stock',
            payload: { stock_code: alert.stockCode },
          },
        });
        this.context.log.info(
          `[dsa-plugin] 已推送告警: ${alert.stockCode} (${alert.alertType})`,
        );
      } else {
        this.context.log.info(
          `[dsa-plugin] 告警(无channel): ${alert.stockCode} ${label}\n${body}`,
        );
      }
    } catch (err) {
      this.context.log.error(`[dsa-plugin] 推送告警失败:`, err);
    }
  }

  /** 每天重置告警记录 */
  resetDailyAlerts(): void {
    this.alertedToday.clear();
  }

  private alertKey(code: string): string {
    const today = new Date().toISOString().slice(0, 10);
    return `${today}:${code}`;
  }
}
