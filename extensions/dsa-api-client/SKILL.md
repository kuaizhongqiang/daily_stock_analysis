---
name: "dsa-api-client"
description: "通过 REST API 调用 daily_stock_analysis 的分析能力。支持股票分析、行情、股池、搜索等。"
---

# DSA API Client

通过 TypeScript SDK 调用 daily_stock_analysis REST API。

## 安装

```bash
npm install dsa-api-client
```

## 使用

```typescript
import { DsaClient } from 'dsa-api-client';
const dsa = new DsaClient({ baseUrl: 'http://localhost:8000' });

const report = await dsa.analyzeStock('600519');
console.log(report.report.summary);
```

## 可用方法

分析: `analyzeStock()`, `checkJobStatus()`
行情: `getStockQuote()`, `resolveStock()`, `getStockBatch()`
大盘: `getMarketStatus()`, `runMarketReview()`
股池: `listPools()`, `createPool()`, `addStockToPool()`, `removeStockFromPool()`, `deletePool()`
搜索: `semanticSearch()`
历史: `searchHistory()`, `getHistoryStats()`, `pruneHistory()`
Agent: `agentChat()`
