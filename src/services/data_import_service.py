# -*- coding: utf-8 -*-
"""
===================================
数据导入服务
===================================

职责：
1. 从 CSV/JSON 导入股票列表到股池
2. 批量导入支持
"""

import csv
import io
import json
import logging
from typing import Dict, List, Optional, Tuple

from src.services.stock_pool_service import StockPoolService

logger = logging.getLogger(__name__)


class DataImportService:
    """数据导入服务。"""

    def __init__(self):
        self.pool_service = StockPoolService()

    def import_stocks_to_pool(self, pool_id: int, data: str,
                               fmt: str = "csv") -> Tuple[int, List[str]]:
        """从 CSV/JSON 导入股票到指定股池。

        Args:
            pool_id: 目标股池 ID
            data: CSV/JSON 字符串
            fmt: csv (code,market 列) 或 json ([{code,market}])

        Returns:
            (成功数, 错误消息列表)
        """
        success = 0
        errors: List[str] = []

        try:
            if fmt == "json":
                records = json.loads(data)
                if isinstance(records, dict):
                    records = [records]
            else:
                records = self._parse_csv(data)

            for rec in records:
                code = rec.get("code", "").strip()
                market = rec.get("market", "cn").strip()
                if not code:
                    errors.append("跳过空代码")
                    continue
                ok = self.pool_service.add_stock(pool_id, code, market, "import")
                if ok:
                    success += 1
                else:
                    errors.append(f"添加 {code} 失败")

            return success, errors

        except Exception as e:
            logger.error("[Import] 导入失败: %s", e)
            return success, [str(e)]

    def _parse_csv(self, data: str) -> List[Dict[str, str]]:
        """解析 CSV 字符串。"""
        reader = csv.DictReader(io.StringIO(data))
        return list(reader)
