# -*- coding: utf-8 -*-
"""
===================================
数据质量日志数据访问层
===================================

职责：
1. 封装 DataQualityLog 表的数据库操作
2. 提供质量日志记录与查询
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy import select, func, and_

from src.storage import DatabaseManager, DataQualityLog

logger = logging.getLogger(__name__)


class DataQualityRepository:
    """
    数据质量日志数据访问层
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager.get_instance()

    def record(self, table_name: str, entity_key: str, data_source: str,
               fetch_status: str, records_fetched: int = 0,
               freshness_score: float = 0.0, reliability_score: float = 0.0,
               error_message: str = "", latency_ms: int = 0) -> bool:
        """记录一条数据获取质量日志。"""
        try:

            def _record(session):
                log = DataQualityLog(
                    table_name=table_name,
                    entity_key=entity_key,
                    data_source=data_source,
                    fetch_status=fetch_status,
                    records_fetched=records_fetched,
                    freshness_score=freshness_score,
                    reliability_score=reliability_score,
                    error_message=error_message,
                    latency_ms=latency_ms,
                )
                session.add(log)
                return True

            return self.db._run_write_transaction("record_data_quality", _record)
        except Exception as e:
            logger.error(f"记录数据质量日志失败: {e}")
            return False

    def get_recent(self, entity_key: str, days: int = 7, limit: int = 50) -> List[DataQualityLog]:
        """获取某个实体的近期质量日志。"""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            with self.db.get_session() as session:
                rows = session.execute(
                    select(DataQualityLog)
                    .where(and_(
                        DataQualityLog.entity_key == entity_key,
                        DataQualityLog.created_at >= cutoff,
                    ))
                    .order_by(DataQualityLog.created_at.desc())
                    .limit(limit)
                ).scalars().all()
                return list(rows)
        except Exception as e:
            logger.error(f"获取数据质量日志失败: {e}")
            return []

    def get_summary(self, days: int = 7) -> dict:
        """获取全局质量概览。"""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            with self.db.get_session() as session:
                total = session.execute(
                    select(func.count(DataQualityLog.id))
                    .where(DataQualityLog.created_at >= cutoff)
                ).scalar() or 0
                success = session.execute(
                    select(func.count(DataQualityLog.id))
                    .where(and_(
                        DataQualityLog.created_at >= cutoff,
                        DataQualityLog.fetch_status == 'success',
                    ))
                ).scalar() or 0
                failed = session.execute(
                    select(func.count(DataQualityLog.id))
                    .where(and_(
                        DataQualityLog.created_at >= cutoff,
                        DataQualityLog.fetch_status == 'failed',
                    ))
                ).scalar() or 0
                return {
                    "total_logs": total,
                    "success_count": success,
                    "failed_count": failed,
                    "success_rate": round(success / total, 4) if total > 0 else 0,
                    "days": days,
                }
        except Exception as e:
            logger.error(f"获取数据质量概览失败: {e}")
            return {"total_logs": 0, "success_count": 0, "failed_count": 0, "success_rate": 0, "days": days}
