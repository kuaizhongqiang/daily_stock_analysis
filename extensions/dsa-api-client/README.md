# dsa-api-client

[![npm version](https://img.shields.io/npm/v/dsa-api-client)](https://www.npmjs.com/package/dsa-api-client)

TypeScript REST API client for [daily_stock_analysis](https://github.com/kuaizhongqiang/daily_stock_analysis). Zero dependencies, works in Node.js 18+ and browsers.

## Install

```bash
npm install dsa-api-client
```

## Usage

```typescript
import { DsaClient } from 'dsa-api-client';

const dsa = new DsaClient({ baseUrl: 'http://localhost:8000' });

// Analyze a stock
const report = await dsa.analyzeStock('600519');
console.log(report.report.summary.operation_advice);

// Get real-time quote
const quote = await dsa.getStockQuote('AAPL');
console.log(quote.price, quote.change_pct);

// Semantic search
const results = await dsa.semanticSearch('白酒龙头');
console.log(results.results);

// Pool management
const pools = await dsa.listPools();
const pool = await dsa.createPool('强势股跟踪');
await dsa.addStockToPool(pool.id, '600519');

// History
const stats = await dsa.getHistoryStats();
const history = await dsa.searchHistory('茅台');

// Agent chat
const reply = await dsa.agentChat('用缠论分析 600519');
```

## API

See [DSA API docs](https://github.com/kuaizhongqiang/daily_stock_analysis) for endpoint details.

## License

MIT
