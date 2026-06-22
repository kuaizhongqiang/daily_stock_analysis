/**
 * DSA API HTTP 客户端
 *
 * 封装与 daily_stock_analysis REST API 的所有通信。
 * 支持超时、重试、错误标准化。
 */

// ============================================================
// 类型定义
// ============================================================

export interface DsaConfig {
  baseUrl: string;
  requestTimeout: number;
}

export interface ApiError {
  status: number;
  code: string;
  message: string;
  detail?: string;
}

export class DsaApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public detail?: string,
  ) {
    super(message);
    this.name = 'DsaApiError';
  }
}

// ============================================================
// 响应类型（简化版，与 DSA API 对齐）
// ============================================================

export interface AnalysisResponse {
  query_id: string;
  stock_code: string;
  stock_name: string;
  report: {
    summary: {
      analysis_summary: string;
      operation_advice: string;
      action: string;
      action_label: string;
      trend_prediction: string;
      sentiment_score: number;
    };
    strategy: {
      ideal_buy: string;
      stop_loss: string;
      take_profit: string;
    };
    technical_analysis?: Record<string, unknown>;
    news_analysis?: Record<string, unknown>;
  };
  created_at: string;
}

export interface StockQuote {
  code: string;
  name: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
  amount: number;
  high: number;
  low: number;
  open: number;
  prev_close: number;
  time: string;
}

export interface MarketStatus {
  indices: Array<{
    code: string;
    name: string;
    price: number;
    change_pct: number;
  }>;
  leading_sectors: string[];
  summary: string;
}

export interface PoolItem {
  id: string;
  name: string;
  description?: string;
  stock_count: number;
  created_at: string;
}

export interface HistoryRecord {
  id: string;
  stock_code: string;
  stock_name: string;
  analysis_summary: string;
  operation_advice: string;
  created_at: string;
}

export interface HistoryStats {
  total_count: number;
  stocks_covered: number;
  date_range: { start: string; end: string };
  actions: Record<string, number>;
}

export interface SearchResult {
  results: Array<{
    stock_code: string;
    stock_name: string;
    relevance: number;
    summary: string;
  }>;
}

export interface JobStatus {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: number;
  result?: AnalysisResponse;
  error?: string;
}

// ============================================================
// HTTP 客户端
// ============================================================

export class DsaClient {
  private baseUrl: string;
  private timeout: number;

  constructor(config: DsaConfig) {
    this.baseUrl = config.baseUrl.replace(/\/+$/, '');
    this.timeout = config.requestTimeout;
  }

  /** 通用请求方法 */
  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    options?: { timeout?: number },
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(
      () => controller.abort(),
      options?.timeout ?? this.timeout,
    );

    try {
      const res = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      if (!res.ok) {
        const errBody = (await res.json().catch(() => ({}))) as Record<
          string,
          string | undefined
        >;
        throw new DsaApiError(
          res.status,
          errBody.error || 'unknown_error',
          errBody.message || `HTTP ${res.status}`,
          errBody.detail,
        );
      }

      return (await res.json()) as T;
    } catch (err) {
      if (err instanceof DsaApiError) throw err;
      if ((err as Error).name === 'AbortError') {
        throw new DsaApiError(408, 'timeout', `请求超时 (${this.timeout}ms)`);
      }
      throw new DsaApiError(
        0,
        'connection_failed',
        `无法连接到 DSA 服务: ${(err as Error).message}。请确认 DSA 已启动 (python main.py --serve-only)`,
      );
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // -------- 分析 API --------

  /** 触发股票分析（同步模式，等待结果） */
  analyzeStock(
    stockCode: string,
    options?: {
      reportType?: string;
      forceRefresh?: boolean;
      skills?: string[];
    },
  ): Promise<AnalysisResponse> {
    return this.request<AnalysisResponse>('POST', '/api/v1/analysis/analyze', {
      stock_code: stockCode,
      report_type: options?.reportType ?? 'detailed',
      force_refresh: options?.forceRefresh ?? false,
      async_mode: false,
      skills: options?.skills,
    });
  }

  /** 触发异步分析，返回 task_id */
  analyzeStockAsync(
    stockCode: string,
    options?: {
      reportType?: string;
      forceRefresh?: boolean;
      skills?: string[];
    },
  ): Promise<{ task_id: string }> {
    return this.request<{ task_id: string }>(
      'POST',
      '/api/v1/analysis/analyze',
      {
        stock_code: stockCode,
        report_type: options?.reportType ?? 'detailed',
        force_refresh: options?.forceRefresh ?? false,
        async_mode: true,
        skills: options?.skills,
      },
    );
  }

  /** 查询异步任务状态 */
  checkJobStatus(taskId: string): Promise<JobStatus> {
    return this.request<JobStatus>(
      'GET',
      `/api/v1/analysis/status/${taskId}`,
    );
  }

  // -------- 行情 API --------

  /** 获取实时行情 */
  getStockQuote(stockCode: string): Promise<StockQuote> {
    return this.request<StockQuote>(
      'GET',
      `/api/v1/stocks/${encodeURIComponent(stockCode)}/quote`,
    );
  }

  /** 解析股票代码 */
  resolveStock(query: string): Promise<{ code: string; name: string; market: string }> {
    return this.request<{ code: string; name: string; market: string }>(
      'GET',
      `/api/v1/stocks/resolve?q=${encodeURIComponent(query)}`,
    );
  }

  /** 批量获取行情 */
  getStockBatch(codes: string[]): Promise<StockQuote[]> {
    return this.request<StockQuote[]>('POST', '/api/v1/stocks/batch', {
      codes,
    });
  }

  // -------- 大盘 API --------

  /** 获取大盘行情 */
  getMarketStatus(): Promise<MarketStatus> {
    return this.request<MarketStatus>('GET', '/api/v1/market/status');
  }

  /** 执行大盘复盘 */
  runMarketReview(): Promise<{ summary: string; sections: Array<{ title: string; content: string }> }> {
    return this.request('POST', '/api/v1/market/review') as Promise<any>;
  }

  // -------- 股池 API --------

  /** 列出股池 */
  listPools(): Promise<PoolItem[]> {
    return this.request<PoolItem[]>('GET', '/api/v1/pools');
  }

  /** 创建股池 */
  createPool(name: string, description?: string): Promise<PoolItem> {
    return this.request<PoolItem>('POST', '/api/v1/pools', {
      name,
      description,
    });
  }

  /** 获取股池详情 */
  getPool(id: string): Promise<PoolItem & { stocks: string[] }> {
    return this.request<PoolItem & { stocks: string[] }>(
      'GET',
      `/api/v1/pools/${encodeURIComponent(id)}`,
    );
  }

  /** 删除股池 */
  deletePool(id: string): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>(
      'DELETE',
      `/api/v1/pools/${encodeURIComponent(id)}`,
    );
  }

  /** 添加股票到股池 */
  addStockToPool(
    poolId: string,
    stockCode: string,
  ): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>(
      'POST',
      `/api/v1/pools/${encodeURIComponent(poolId)}/stocks`,
      { stock_code: stockCode },
    );
  }

  /** 从股池移除股票 */
  removeStockFromPool(
    poolId: string,
    stockCode: string,
  ): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>(
      'DELETE',
      `/api/v1/pools/${encodeURIComponent(poolId)}/stocks`,
      { stock_code: stockCode },
    );
  }

  // -------- 搜索 API --------

  /** 语义搜索 */
  semanticSearch(
    query: string,
    limit?: number,
  ): Promise<SearchResult> {
    const params = new URLSearchParams({ query });
    if (limit) params.set('limit', String(limit));
    return this.request<SearchResult>(
      'GET',
      `/api/v1/search/semantic?${params}`,
    );
  }

  /** 搜索索引状态 */
  getVectorIndexStatus(): Promise<{ status: string; document_count: number }> {
    return this.request('GET', '/api/v1/search/status') as Promise<any>;
  }

  // -------- 历史 API --------

  /** 搜索历史分析 */
  searchHistory(
    query: string,
    limit?: number,
  ): Promise<HistoryRecord[]> {
    const params = new URLSearchParams({ query });
    if (limit) params.set('limit', String(limit));
    return this.request<HistoryRecord[]>(
      'GET',
      `/api/v1/history/search?${params}`,
    );
  }

  /** 历史统计 */
  getHistoryStats(): Promise<HistoryStats> {
    return this.request<HistoryStats>('GET', '/api/v1/history/stats');
  }

  /** 导出历史 */
  exportHistory(fmt?: string): Promise<string> {
    return this.request<string>(
      'GET',
      `/api/v1/history/export?fmt=${fmt ?? 'json'}`,
    );
  }

  /** 清理旧历史 */
  pruneHistory(olderThanDays: number): Promise<{ deleted: number }> {
    return this.request<{ deleted: number }>(
      'DELETE',
      `/api/v1/history/prune?older_than_days=${olderThanDays}`,
    );
  }

  // -------- Agent API --------

  /** Agent 策略问股 */
  agentChat(
    message: string,
    sessionId?: string,
  ): Promise<{ content: string; session_id: string }> {
    return this.request<{ content: string; session_id: string }>(
      'POST',
      '/api/v1/agent/chat',
      { message, session_id: sessionId },
      // Agent 问股通常较快，使用常规超时
    );
  }
}
