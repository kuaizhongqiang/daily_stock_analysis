# -*- coding: utf-8 -*-
"""
===================================
数据质量业务逻辑层
===================================

职责：
1. 记录数据获取质量
2. 生成质量报告
"""

import logging
from typing import Optional, Dict, Any

from src.repositories.data_quality_repo import DataQualityRepository

logger = logging.getLogger(__name__)


class DataQualityService:
    """
    数据质量业务逻辑层
    """

    def __init__(self):
        self.repo = DataQualityRepository()

    def record_fetch(self, table_name: str, entity_key: str, data_source: str,
                     success: bool, records_fetched: int = 0,
                     freshness_score: float = 0.0, reliability_score: float = 0.0,
                     error_message: str = "", latency_ms: int = 0) -> bool:
        """记录一次数据获取的质量。"""
        status = "success" if success else "failed"
        return self.repo.record(
            table_name=table_name,
            entity_key=entity_key,
            data_source=data_source,
            fetch_status=status,
            records_fetched=records_fetched,
            freshness_score=freshness_score,
            reliability_score=reliability_score,
            error_message=error_message,
            latency_ms=latency_ms,
        )

    def get_report(self, entity_key: str, days: int = 7) -> Dict[str, Any]:
        """获取某个实体的质量报告。"""
        logs = self.repo.get_recent(entity_key, days)
        if not logs:
            return {"entity_key": entity_key, "days": days, "total_entries": 0, "entries": []}

        success_count = sum(1 for l in logs if l.fetch_status == "success")
        failed_count = sum(1 for l in logs if l.fetch_status == "failed")
        avg_latency = sum(l.latency_ms or 0 for l in logs) / len(logs) if logs else 0

        return {
            "entity_key": entity_key,
            "days": days,
            "total_entries": len(logs),
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": round(success_count / len(logs), 4) if logs else 0,
            "avg_latency_ms": round(avg_latency, 1),
            "entries": [
                {
                    "table_name": l.table_name,
                    "data_source": l.data_source,
                    "fetch_status": l.fetch_status,
                    "records_fetched": l.records_fetched,
                    "freshness_score": l.freshness_score,
                    "latency_ms": l.latency_ms,
                    "created_at": l.created_at.isoformat() if l.created_at else None,
                }
                for l in logs[:20]
            ],
        }

    def get_global_summary(self, days: int = 7) -> Dict[str, Any]:
        """获取全局质量概览。"""
        summary = self.repo.get_summary(days)
        return summary
