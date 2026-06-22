/**
 * dsa-api-client — TypeScript REST API 客户端
 *
 * 零依赖，基于 fetch，Node.js 18+ / 浏览器兼容。
 * 覆盖 daily_stock_analysis 所有 API 端点。
 */

// ============================================================
// 类型定义
// ============================================================

export interface DsaClientConfig {
  baseUrl: string;
  requestTimeout?: number;
  token?: string;
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

// ---- 响应类型 ----

export interface AnalysisReport {
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
  indices: Array<{ code: string; name: string; price: number; change_pct: number }>;
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
  result?: AnalysisReport;
  error?: string;
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
  actions: Record<string, number>;
}

// ============================================================
// 客户端
// ============================================================

export class DsaClient {
  private baseUrl: string;
  private timeout: number;
  private token?: string;

  constructor(config: DsaClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/+$/, '');
    this.timeout = config.requestTimeout ?? 300_000;
    this.token = config.token;
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    options?: { timeout?: number },
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), options?.timeout ?? this.timeout);

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      };
      if (this.token) headers['Authorization'] = `Bearer ${this.token}`;

      const res = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      if (!res.ok) {
        const errBody = (await res.json().catch(() => ({}))) as Record<string, string | undefined>;
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
        throw new DsaApiError(408, 'timeout', `Request timed out after ${this.timeout}ms`);
      }
      throw new DsaApiError(
        0,
        'connection_failed',
        `Cannot connect to DSA: ${(err as Error).message}. Ensure DSA is running (python main.py --serve-only)`,
      );
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // ======================== 分析 ========================

  analyzeStock(stockCode: string, options?: {
    reportType?: string; forceRefresh?: boolean; skills?: string[];
  }): Promise<AnalysisReport> {
    return this.request<AnalysisReport>('POST', '/api/v1/analysis/analyze', {
      stock_code: stockCode,
      report_type: options?.reportType ?? 'detailed',
      force_refresh: options?.forceRefresh ?? false,
      async_mode: false,
      skills: options?.skills,
    });
  }

  analyzeStockAsync(stockCode: string, options?: {
    reportType?: string; forceRefresh?: boolean;
  }): Promise<{ task_id: string }> {
    return this.request<{ task_id: string }>('POST', '/api/v1/analysis/analyze', {
      stock_code: stockCode,
      report_type: options?.reportType ?? 'detailed',
      force_refresh: options?.forceRefresh ?? false,
      async_mode: true,
    });
  }

  checkJobStatus(taskId: string): Promise<JobStatus> {
    return this.request<JobStatus>('GET', `/api/v1/analysis/status/${taskId}`);
  }

  // ======================== 行情 ========================

  getStockQuote(stockCode: string): Promise<StockQuote> {
    return this.request<StockQuote>('GET', `/api/v1/stocks/${encodeURIComponent(stockCode)}/quote`);
  }

  resolveStock(query: string): Promise<{ code: string; name: string; market: string }> {
    return this.request('GET', `/api/v1/stocks/resolve?q=${encodeURIComponent(query)}`);
  }

  getStockBatch(codes: string[]): Promise<StockQuote[]> {
    return this.request<StockQuote[]>('POST', '/api/v1/stocks/batch', { codes });
  }

  // ======================== 大盘 ========================

  getMarketStatus(): Promise<MarketStatus> {
    return this.request<MarketStatus>('GET', '/api/v1/market/status');
  }

  runMarketReview(): Promise<{ summary: string; sections: Array<{ title: string; content: string }> }> {
    return this.request('POST', '/api/v1/market/review');
  }

  // ======================== 股池 ========================

  listPools(): Promise<PoolItem[]> {
    return this.request<PoolItem[]>('GET', '/api/v1/pools');
  }

  createPool(name: string, description?: string): Promise<PoolItem> {
    return this.request<PoolItem>('POST', '/api/v1/pools', { name, description });
  }

  getPool(id: string): Promise<PoolItem & { stocks: string[] }> {
    return this.request('GET', `/api/v1/pools/${encodeURIComponent(id)}`);
  }

  deletePool(id: string): Promise<{ success: boolean }> {
    return this.request('DELETE', `/api/v1/pools/${encodeURIComponent(id)}`);
  }

  addStockToPool(poolId: string, stockCode: string): Promise<{ success: boolean }> {
    return this.request('POST', `/api/v1/pools/${encodeURIComponent(poolId)}/stocks`, {
      stock_code: stockCode,
    });
  }

  removeStockFromPool(poolId: string, stockCode: string): Promise<{ success: boolean }> {
    return this.request('DELETE', `/api/v1/pools/${encodeURIComponent(poolId)}/stocks`, {
      stock_code: stockCode,
    });
  }

  // ======================== 搜索 ========================

  semanticSearch(query: string, limit?: number): Promise<SearchResult> {
    const params = new URLSearchParams({ query });
    if (limit) params.set('limit', String(limit));
    return this.request<SearchResult>('GET', `/api/v1/search/semantic?${params}`);
  }

  getVectorIndexStatus(): Promise<{ status: string; document_count: number }> {
    return this.request('GET', '/api/v1/search/status');
  }

  // ======================== 历史 ========================

  searchHistory(query: string, limit?: number): Promise<HistoryRecord[]> {
    const params = new URLSearchParams({ query });
    if (limit) params.set('limit', String(limit));
    return this.request<HistoryRecord[]>('GET', `/api/v1/history/search?${params}`);
  }

  getHistoryStats(): Promise<HistoryStats> {
    return this.request<HistoryStats>('GET', '/api/v1/history/stats');
  }

  exportHistory(fmt?: string): Promise<string> {
    return this.request<string>('GET', `/api/v1/history/export?fmt=${fmt ?? 'json'}`);
  }

  pruneHistory(olderThanDays: number): Promise<{ deleted: number }> {
    return this.request('DELETE', `/api/v1/history/prune?older_than_days=${olderThanDays}`);
  }

  // ======================== Agent ========================

  agentChat(message: string, sessionId?: string): Promise<{ content: string; session_id: string }> {
    return this.request('POST', '/api/v1/agent/chat', { message, session_id: sessionId });
  }
}
