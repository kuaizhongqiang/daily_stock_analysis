# -*- coding: utf-8 -*-
"""
===================================
股票数据服务层
===================================

职责：
1. 封装股票数据获取逻辑
2. 提供实时行情和历史数据接口
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from src.repositories.stock_repo import StockRepository

logger = logging.getLogger(__name__)


class StockService:
    """
    股票数据服务
    
    封装股票数据获取的业务逻辑
    """
    
    def __init__(self):
        """初始化股票数据服务"""
        self.repo = StockRepository()
    
    def get_realtime_quote(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取股票实时行情

        优先级：
        1. DataFetcherManager 实时行情（外部数据源 efinance/akshare 等）
        2. 数据库 stock_daily 最新日线降级兜底
        3. 占位数据（仅当 DataFetcherManager 不可导入时）

        Args:
            stock_code: 股票代码

        Returns:
            实时行情数据字典
        """
        try:
            from data_provider.base import DataFetcherManager

            manager = DataFetcherManager()
            quote = manager.get_realtime_quote(stock_code)

            if quote is not None:
                # UnifiedRealtimeQuote 是 dataclass，使用 getattr 安全访问字段
                # 字段映射: UnifiedRealtimeQuote -> API 响应
                # - code -> stock_code
                # - name -> stock_name
                # - price -> current_price
                # - change_amount -> change
                # - change_pct -> change_percent
                # - open_price -> open
                # - high -> high
                # - low -> low
                # - pre_close -> prev_close
                # - volume -> volume
                # - amount -> amount
                return {
                    "stock_code": getattr(quote, "code", stock_code),
                    "stock_name": getattr(quote, "name", None),
                    "current_price": getattr(quote, "price", 0.0) or 0.0,
                    "change": getattr(quote, "change_amount", None),
                    "change_percent": getattr(quote, "change_pct", None),
                    "open": getattr(quote, "open_price", None),
                    "high": getattr(quote, "high", None),
                    "low": getattr(quote, "low", None),
                    "prev_close": getattr(quote, "pre_close", None),
                    "volume": getattr(quote, "volume", None),
                    "amount": getattr(quote, "amount", None),
                    "update_time": datetime.now().isoformat(),
                }

            # 降级: 外部数据源不可用时，从数据库 stock_daily 取最新日线
            logger.info("[实时行情] 外部数据源不可用，从数据库降级获取 %s", stock_code)
            return self._get_db_quote_fallback(stock_code, manager=manager)

        except ImportError:
            logger.warning("DataFetcherManager 未找到，使用占位数据")
            return self._get_placeholder_quote(stock_code)
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}", exc_info=True)
            return None

    def _get_db_quote_fallback(
        self,
        stock_code: str,
        manager: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        从数据库 stock_daily 获取最新日线作为行情降级方案。

        当外部实时数据源不可用时，使用最近的日线数据构造行情响应，
        确保下游（如 personal-helper-server）仍能获取价格和涨跌幅。

        Args:
            stock_code: 股票代码
            manager: 可选的 DataFetcherManager 实例（用于获取股票名称）

        Returns:
            行情数据字典，或 None（无数据库记录时）
        """
        try:
            records = self.repo.get_latest(stock_code, days=2)
            if not records:
                logger.warning("[数据库降级] %s 无数据库记录", stock_code)
                return None

            latest = records[0]
            if latest.close is None:
                logger.warning("[数据库降级] %s 最新日线 close 为空", stock_code)
                return None

            close_val = float(latest.close)

            # 计算 prev_close 和 change
            if latest.pct_chg is not None:
                prev_close = round(close_val / (1 + float(latest.pct_chg) / 100), 2)
                change = round(close_val - prev_close, 2)
            elif len(records) >= 2 and records[1].close is not None:
                prev_close = float(records[1].close)
                change = round(close_val - prev_close, 2)
            else:
                prev_close = close_val
                change = None

            result: Dict[str, Any] = {
                "stock_code": stock_code,
                "stock_name": None,
                "current_price": close_val,
                "change": change,
                "change_percent": float(latest.pct_chg) if latest.pct_chg is not None else None,
                "open": float(latest.open) if latest.open is not None else None,
                "high": float(latest.high) if latest.high is not None else None,
                "low": float(latest.low) if latest.low is not None else None,
                "prev_close": prev_close,
                "volume": float(latest.volume) if latest.volume is not None else None,
                "amount": float(latest.amount) if latest.amount is not None else None,
                "update_time": latest.date.isoformat() if latest.date else None,
            }

            # 尝试获取股票名称
            if manager is not None and hasattr(manager, "get_stock_name"):
                try:
                    name = manager.get_stock_name(stock_code)
                    if name:
                        result["stock_name"] = name
                except Exception:
                    pass

            logger.info(
                "[数据库降级] %s 行情构造成功: price=%s, pct_chg=%s, date=%s",
                stock_code, result["current_price"], result["change_percent"], result["update_time"],
            )
            return result

        except Exception as e:
            logger.error("[数据库降级] %s 构造失败: %s", stock_code, e)
            return None
    
    def get_history_data(
        self,
        stock_code: str,
        period: str = "daily",
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取股票历史行情
        
        Args:
            stock_code: 股票代码
            period: K 线周期 (daily/weekly/monthly)
            days: 获取天数
            
        Returns:
            历史行情数据字典
            
        Raises:
            ValueError: 当 period 不是 daily 时抛出（weekly/monthly 暂未实现）
        """
        # 验证 period 参数，只支持 daily
        if period != "daily":
            raise ValueError(
                f"暂不支持 '{period}' 周期，目前仅支持 'daily'。"
                "weekly/monthly 聚合功能将在后续版本实现。"
            )
        
        try:
            # 调用数据获取器获取历史数据
            from data_provider.base import DataFetcherManager
            
            manager = DataFetcherManager()
            df, source = manager.get_daily_data(stock_code, days=days)
            
            if df is None or df.empty:
                logger.warning(f"获取 {stock_code} 历史数据失败")
                return {"stock_code": stock_code, "period": period, "data": []}
            
            # 获取股票名称
            stock_name = manager.get_stock_name(stock_code)
            
            # 转换为响应格式
            data = []
            for _, row in df.iterrows():
                date_val = row.get("date")
                if hasattr(date_val, "strftime"):
                    date_str = date_val.strftime("%Y-%m-%d")
                else:
                    date_str = str(date_val)
                
                data.append({
                    "date": date_str,
                    "open": float(row.get("open", 0)),
                    "high": float(row.get("high", 0)),
                    "low": float(row.get("low", 0)),
                    "close": float(row.get("close", 0)),
                    "volume": float(row.get("volume", 0)) if row.get("volume") else None,
                    "amount": float(row.get("amount", 0)) if row.get("amount") else None,
                    "change_percent": float(row.get("pct_chg", 0)) if row.get("pct_chg") else None,
                })
            
            return {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "period": period,
                "data": data,
            }
            
        except ImportError:
            logger.warning("DataFetcherManager 未找到，返回空数据")
            return {"stock_code": stock_code, "period": period, "data": []}
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}", exc_info=True)
            return {"stock_code": stock_code, "period": period, "data": []}
    
    def _get_placeholder_quote(self, stock_code: str) -> Dict[str, Any]:
        """
        获取占位行情数据（用于测试）
        
        Args:
            stock_code: 股票代码
            
        Returns:
            占位行情数据
        """
        return {
            "stock_code": stock_code,
            "stock_name": f"股票{stock_code}",
            "current_price": 0.0,
            "change": None,
            "change_percent": None,
            "open": None,
            "high": None,
            "low": None,
            "prev_close": None,
            "volume": None,
            "amount": None,
            "update_time": datetime.now().isoformat(),
        }
