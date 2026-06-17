# -*- coding: utf-8 -*-
"""
===================================
数据导出服务
===================================

职责：
1. 分析历史导出 (JSON/CSV)
2. 股票数据导出
3. 会话对话导出
"""

import csv
import io
import json
import logging
from typing import Optional

from src.storage import DatabaseManager, AnalysisHistory, ConversationMessage

logger = logging.getLogger(__name__)


class DataExportService:
    """数据导出服务。"""

    def __init__(self):
        self.db = DatabaseManager.get_instance()

    def export_analysis(self, code: Optional[str] = None,
                        days: int = 30, fmt: str = "json") -> str:
        """导出分析历史。"""
        from src.services.history_retention_service import HistoryRetentionService
        svc = HistoryRetentionService()
        if fmt == "csv":
            return svc.export_analysis_csv(days=days, code=code)
        return svc.export_analysis_json(days=days, code=code)

    def download_csv(self, code: str, days: int = 60) -> Optional[str]:
        """下载股票日线数据为 CSV。"""
        try:
            from data_provider import DataFetcherManager
            import pandas as pd

            manager = DataFetcherManager()
            df = manager.get_daily_data(code, days=days)
            if df is None or df.empty:
                return None
            output = io.StringIO()
            df.to_csv(output, index=False, encoding="utf-8-sig")
            return output.getvalue()
        except Exception as e:
            logger.error("[Export] 下载 CSV 失败: %s", e)
            return None
