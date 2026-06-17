# -*- coding: utf-8 -*-
"""
===================================
股票元数据业务逻辑层
===================================

职责：
1. 封装元数据 CRUD 逻辑
2. 通过 DataFetcherManager 自动补全元数据
"""

import json
import logging
from typing import Optional, List, Dict, Any

from src.repositories.stock_metadata_repo import StockMetadataRepository

logger = logging.getLogger(__name__)


class StockMetadataService:
    """
    股票元数据业务逻辑层
    """

    def __init__(self):
        self.repo = StockMetadataRepository()

    def get(self, code: str) -> Optional[Dict[str, Any]]:
        """获取单只股票的元数据。"""
        meta = self.repo.get(code)
        if meta is None:
            return None
        return self._meta_to_dict(meta)

    def upsert(self, code: str, **kwargs) -> bool:
        """插入或更新元数据。"""
        return self.repo.upsert(code, **kwargs)

    def enrich_from_fetcher(self, code: str, name: str = "", market: str = "cn") -> bool:
        """通过 DataFetcherManager 自动补充元数据。"""
        try:
            from data_provider import DataFetcherManager
            manager = DataFetcherManager()
            ctx = manager.get_fundamental_context(code)
            if not ctx or not isinstance(ctx, dict):
                logger.warning(f"无法从数据源获取 {code} 的元数据")
                return False

            coverage = ctx.get("coverage", {})
            data_sources = coverage.get("data_sources", [])
            source_chain = ",".join(data_sources) if isinstance(data_sources, list) else str(data_sources)

            valuation = ctx.get("valuation", {}).get("data", {}) or {}
            return self.repo.upsert(
                code,
                name=name or valuation.get("name", ""),
                market=market,
                sector=valuation.get("sector", ""),
                industry=valuation.get("industry", ""),
                total_market_cap=valuation.get("total_market_cap"),
                circulating_market_cap=valuation.get("circulating_market_cap"),
                metadata_json=json.dumps(ctx, ensure_ascii=False),
                data_source=source_chain,
            )
        except Exception as e:
            logger.warning(f"自动补充元数据失败 {code}: {e}")
            return False

    def list_by_sector(self, sector: str) -> List[Dict[str, Any]]:
        """按行业板块列出股票。"""
        return [self._meta_to_dict(m) for m in self.repo.list_by_sector(sector)]

    def list_all(self, limit: int = 200, offset: int = 0) -> List[Dict[str, Any]]:
        """列出所有元数据。"""
        return [self._meta_to_dict(m) for m in self.repo.list_all(limit, offset)]

    def _meta_to_dict(self, meta) -> Dict[str, Any]:
        return {
            "code": meta.code,
            "name": meta.name,
            "market": meta.market,
            "sector": meta.sector,
            "industry": meta.industry,
            "total_market_cap": meta.total_market_cap,
            "circulating_market_cap": meta.circulating_market_cap,
            "listing_date": meta.listing_date.isoformat() if meta.listing_date else None,
            "is_active": meta.is_active,
            "data_source": meta.data_source,
            "updated_at": meta.updated_at.isoformat() if meta.updated_at else None,
        }
