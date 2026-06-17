# -*- coding: utf-8 -*-
"""
===================================
股池业务逻辑层
===================================

职责：
1. 封装股池 CRUD 业务逻辑
2. 通过 DataFetcherManager 补充股票名称信息
"""

import logging
from typing import Optional, List, Dict, Any

from src.repositories.stock_pool_repo import StockPoolRepository
from src.repositories.stock_metadata_repo import StockMetadataRepository

logger = logging.getLogger(__name__)


class StockPoolService:
    """
    股池业务逻辑层
    """

    def __init__(self):
        self.pool_repo = StockPoolRepository()
        self.metadata_repo = StockMetadataRepository()

    # ---- Pool CRUD ----

    def create_pool(self, name: str, description: str = "", tags: str = "") -> Optional[Dict[str, Any]]:
        """创建股池。"""
        pool = self.pool_repo.create_pool(name, description, tags)
        return pool

    def get_pool(self, pool_id: int) -> Optional[Dict[str, Any]]:
        """获取股池详情。"""
        pool = self.pool_repo.get_pool(pool_id)
        if pool is None:
            return None
        count = self.pool_repo.get_member_count(pool_id)
        return self._pool_to_dict(pool, count)

    def list_pools(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """列出股池（批量查询减少 N+1）。"""
        pools = self.pool_repo.list_pools(active_only)
        if not pools:
            return []
        pool_ids = [p.id for p in pools]
        counts = self.pool_repo.get_member_counts(pool_ids)
        return [self._pool_to_dict(p, counts.get(p.id, 0)) for p in pools]

    def update_pool(self, pool_id: int, **kwargs) -> bool:
        """更新股池。"""
        return self.pool_repo.update_pool(pool_id, **kwargs)

    def delete_pool(self, pool_id: int) -> bool:
        """删除股池。"""
        return self.pool_repo.delete_pool(pool_id)

    # ---- Pool Members ----

    def add_stock(self, pool_id: int, code: str, market: str = "cn",
                  reason: str = "", added_by: str = "manual") -> bool:
        """向股池添加股票。"""
        return self.pool_repo.add_stock(pool_id, code, market, reason, added_by)

    def remove_stock(self, pool_id: int, code: str) -> bool:
        """从股池移除股票。"""
        return self.pool_repo.remove_stock(pool_id, code)

    def list_stocks(self, pool_id: int) -> List[Dict[str, Any]]:
        """列出股池内股票（附带股票名称）。"""
        members = self.pool_repo.list_stocks(pool_id)
        result = []
        for m in members:
            meta = self.metadata_repo.get(m.code) if m.code else None
            result.append({
                "id": m.id,
                "pool_id": m.pool_id,
                "code": m.code,
                "market": m.market,
                "name": meta.name if meta else "",
                "sector": meta.sector if meta else "",
                "added_reason": m.added_reason,
                "added_by": m.added_by,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            })
        return result

    # ---- Helpers ----

    def _pool_to_dict(self, pool, member_count: int = 0) -> Dict[str, Any]:
        return {
            "id": pool.id,
            "name": pool.name,
            "description": pool.description,
            "tags": pool.tags,
            "is_active": pool.is_active,
            "member_count": member_count,
            "created_at": pool.created_at.isoformat() if pool.created_at else None,
            "updated_at": pool.updated_at.isoformat() if pool.updated_at else None,
        }
