# -*- coding: utf-8 -*-
"""
===================================
股票元数据数据访问层
===================================

职责：
1. 封装 StockMetadata 表的数据库操作
2. 提供元数据查询接口
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, and_

from src.storage import DatabaseManager, StockMetadata

logger = logging.getLogger(__name__)


class StockMetadataRepository:
    """
    股票元数据数据访问层
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager.get_instance()

    def get(self, code: str) -> Optional[StockMetadata]:
        """获取单只股票的元数据。"""
        try:
            with self.db.get_session() as session:
                return session.get(StockMetadata, code)
        except Exception as e:
            logger.error(f"获取股票元数据失败: {e}")
            return None

    def upsert(self, code: str, **kwargs) -> bool:
        """插入或更新股票元数据。"""
        try:

            def _upsert(session):
                existing = session.get(StockMetadata, code)
                if existing:
                    for key, value in kwargs.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.updated_at = datetime.now()
                else:
                    meta = StockMetadata(code=code, **kwargs)
                    session.add(meta)
                return True

            return self.db._run_write_transaction("upsert_stock_metadata", _upsert)
        except Exception as e:
            logger.error(f"更新股票元数据失败: {e}")
            return False

    def list_by_sector(self, sector: str) -> List[StockMetadata]:
        """按行业板块列出股票。"""
        try:
            with self.db.get_session() as session:
                rows = session.execute(
                    select(StockMetadata).where(StockMetadata.sector == sector)
                ).scalars().all()
                return list(rows)
        except Exception as e:
            logger.error(f"按行业板块查询失败: {e}")
            return []

    def list_by_industry(self, industry: str) -> List[StockMetadata]:
        """按行业列出股票。"""
        try:
            with self.db.get_session() as session:
                rows = session.execute(
                    select(StockMetadata).where(StockMetadata.industry == industry)
                ).scalars().all()
                return list(rows)
        except Exception as e:
            logger.error(f"按行业查询失败: {e}")
            return []

    def list_all(self, limit: int = 200, offset: int = 0) -> List[StockMetadata]:
        """列出所有元数据。"""
        try:
            with self.db.get_session() as session:
                rows = session.execute(
                    select(StockMetadata).order_by(StockMetadata.code).offset(offset).limit(limit)
                ).scalars().all()
                return list(rows)
        except Exception as e:
            logger.error(f"列出所有元数据失败: {e}")
            return []
