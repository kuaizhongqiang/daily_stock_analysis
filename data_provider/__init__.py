# -*- coding: utf-8 -*-
"""
===================================
数据源策略层 - 包初始化
===================================

本包实现策略模式管理多个数据源，实现：
1. 统一的数据获取接口
2. 自动故障切换
3. 防封禁流控策略

数据源优先级（动态调整）：
【配置了 TUSHARE_TOKEN 时】
1. TushareFetcher (Priority 0) - 🔥 最高优先级（动态提升）
2. EfinanceFetcher (Priority 0) - 同优先级
3. AkshareFetcher (Priority 1) - 来自 akshare 库
4. PytdxFetcher (Priority 2) - 来自 pytdx 库（通达信）
5. BaostockFetcher (Priority 3) - 来自 baostock 库
6. YfinanceFetcher (Priority 4) - 来自 yfinance 库

【未配置 TUSHARE_TOKEN 时】
1. EfinanceFetcher (Priority 0) - 最高优先级，来自 efinance 库
2. AkshareFetcher (Priority 1) - 来自 akshare 库
3. PytdxFetcher (Priority 2) - 来自 pytdx 库（通达信）
4. TushareFetcher (Priority 2) - 来自 tushare 库（不可用）
5. BaostockFetcher (Priority 3) - 来自 baostock 库
6. YfinanceFetcher (Priority 4) - 来自 yfinance 库
7. LongbridgeFetcher (Priority 5) - 长桥 OpenAPI（美股/港股兜底）

提示：优先级数字越小越优先，同优先级按初始化顺序排列
"""

from .base import BaseFetcher, DataFetcherManager


# 以下 fetcher 使用懒加载（__getattr__），避免模块级 import 触发深层依赖链。
# 仅当实际访问对应类名时才执行 import。
_FETCHER_LAZY_IMPORTS = {
    "EfinanceFetcher": ".efinance_fetcher",
    "AkshareFetcher": ".akshare_fetcher",
    "TushareFetcher": ".tushare_fetcher",
    "PytdxFetcher": ".pytdx_fetcher",
    "BaostockFetcher": ".baostock_fetcher",
    "YfinanceFetcher": ".yfinance_fetcher",
    "LongbridgeFetcher": ".longbridge_fetcher",
    "FinnhubFetcher": ".finnhub_fetcher",
    "AlphaVantageFetcher": ".alphavantage_fetcher",
    "is_hk_stock_code": ".akshare_fetcher",
    "is_us_stock_code": ".us_index_mapping",
    "is_us_index_code": ".us_index_mapping",
    "get_us_index_yf_symbol": ".us_index_mapping",
    "US_INDEX_MAPPING": ".us_index_mapping",
}


def __getattr__(name):
    if name in _FETCHER_LAZY_IMPORTS:
        import importlib
        mod = importlib.import_module(_FETCHER_LAZY_IMPORTS[name], __package__)
        val = getattr(mod, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(__all__)

__all__ = [
    'BaseFetcher',
    'DataFetcherManager',
    'EfinanceFetcher',
    'AkshareFetcher',
    'TushareFetcher',
    'PytdxFetcher',
    'BaostockFetcher',
    'YfinanceFetcher',
    'LongbridgeFetcher',
    'FinnhubFetcher',
    'AlphaVantageFetcher',
    'is_us_index_code',
    'is_us_stock_code',
    'is_hk_stock_code',
    'get_us_index_yf_symbol',
    'US_INDEX_MAPPING',
]
