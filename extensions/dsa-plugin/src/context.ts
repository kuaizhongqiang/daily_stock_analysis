/**
 * 会话上下文管理
 *
 * 支持跨轮对话的状态保持、追问联想、历史引用。
 * 生命周期：Plugin 进程生命周期内有效（内存级，v0.1 不持久化）。
 */

// ============================================================
// 类型定义
// ============================================================

export interface AnalysisResult {
  stockCode: string;
  stockName: string;
  sentimentScore: number;
  action: string;
  actionLabel: string;
  summary: string;
  timestamp: string;
}

export interface PoolReference {
  poolId: string;
  poolName: string;
}

export interface SessionState {
  /** 当前分析的标的（最近一只） */
  currentStock?: {
    code: string;
    name: string;
  };
  /** 本会话中分析过的所有标的 */
  recentStocks: Array<{
    code: string;
    name: string;
    result?: AnalysisResult;
    timestamp: string;
  }>;
  /** 会话中引用过的股池 */
  activePools: PoolReference[];
  /** 最后一条 Agent 回复（用于追问联想） */
  lastAssistantMessage?: string;
  /** 会话创建时间 */
  createdAt: string;
  /** 最后活动时间 */
  lastActiveAt: string;
}

// ============================================================
// 上下文管理器
// ============================================================

export class SessionContextManager {
  /** 会话状态存储（内存） */
  private sessions = new Map<string, SessionState>();

  /** 最大会话数，防止内存泄漏 */
  private maxSessions: number;

  /** 会话空转超时（毫秒），超时自动回收 */
  private idleTimeout: number;

  constructor(options?: { maxSessions?: number; idleTimeout?: number }) {
    this.maxSessions = options?.maxSessions ?? 100;
    this.idleTimeout = options?.idleTimeout ?? 30 * 60 * 1000; // 30 分钟
  }

  /** 获取或创建会话 */
  getOrCreate(sessionId: string): SessionState {
    let session = this.sessions.get(sessionId);
    if (!session) {
      session = {
        recentStocks: [],
        activePools: [],
        createdAt: new Date().toISOString(),
        lastActiveAt: new Date().toISOString(),
      };
      this.sessions.set(sessionId, session);
      this.evictIfNeeded();
    }
    session.lastActiveAt = new Date().toISOString();
    return session;
  }

  /** 获取会话，不存在返回 null */
  get(sessionId: string): SessionState | null {
    const session = this.sessions.get(sessionId);
    if (!session) return null;
    session.lastActiveAt = new Date().toISOString();
    return session;
  }

  /** 设置当前分析标的 */
  setCurrentStock(sessionId: string, code: string, name: string): void {
    const session = this.getOrCreate(sessionId);
    session.currentStock = { code, name };
    // 加入历史（最新在前）
    session.recentStocks = [
      { code, name, timestamp: new Date().toISOString() },
      ...session.recentStocks.filter((s) => s.code !== code),
    ];
  }

  /** 绑定分析结果到标的 */
  setAnalysisResult(
    sessionId: string,
    code: string,
    result: AnalysisResult,
  ): void {
    const session = this.getOrCreate(sessionId);
    const existing = session.recentStocks.find((s) => s.code === code);
    if (existing) {
      existing.result = result;
    }
  }

  /** 记录活跃股池引用 */
  addPoolRef(sessionId: string, poolId: string, poolName: string): void {
    const session = this.getOrCreate(sessionId);
    session.activePools = [
      { poolId, poolName },
      ...session.activePools.filter((p) => p.poolId !== poolId),
    ];
  }

  /** 记录最后一条助手消息 */
  setLastMessage(sessionId: string, message: string): void {
    const session = this.getOrCreate(sessionId);
    session.lastAssistantMessage = message;
  }

  /** 尝试解析追问中的隐含引用（如"那五粮液呢"→对比上一只） */
  resolveFollowUp(sessionId: string): {
    previousStock?: { code: string; name: string };
    previousResult?: AnalysisResult;
  } | null {
    const session = this.get(sessionId);
    if (!session || session.recentStocks.length === 0) return null;

    const prev = session.recentStocks[0];
    return {
      previousStock: prev,
      previousResult: prev.result,
    };
  }

  /** 获取最近 N 只分析过的股票 */
  getRecentStocks(sessionId: string, n: number = 5): SessionState['recentStocks'] {
    const session = this.get(sessionId);
    if (!session) return [];
    return session.recentStocks.slice(0, n);
  }

  /** 删除会话 */
  delete(sessionId: string): void {
    this.sessions.delete(sessionId);
  }

  /** 清理超时会话 */
  cleanIdleSessions(): number {
    const now = Date.now();
    let cleaned = 0;
    for (const [id, session] of this.sessions.entries()) {
      const inactive = now - new Date(session.lastActiveAt).getTime();
      if (inactive > this.idleTimeout) {
        this.sessions.delete(id);
        cleaned++;
      }
    }
    return cleaned;
  }

  /** 会话总数 */
  get size(): number {
    return this.sessions.size;
  }

  /** 超过最大数时淘汰最久未使用的 */
  private evictIfNeeded(): void {
    if (this.sessions.size <= this.maxSessions) return;

    // 按 lastActiveAt 升序排序，删掉最旧的
    const sorted = [...this.sessions.entries()].sort(
      (a, b) =>
        new Date(a[1].lastActiveAt).getTime() -
        new Date(b[1].lastActiveAt).getTime(),
    );

    const toDelete = this.sessions.size - this.maxSessions;
    for (let i = 0; i < toDelete && i < sorted.length; i++) {
      this.sessions.delete(sorted[i][0]);
    }
  }
}

/** 全局单例 */
export const sessionManager = new SessionContextManager();
