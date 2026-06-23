# -*- coding: utf-8 -*-
"""
===================================
股票数据相关模型
===================================

职责：
1. 定义股票实时行情模型
2. 定义历史 K 线数据模型
"""

from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field


class StockQuote(BaseModel):
    """股票实时行情"""
    
    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    current_price: float = Field(..., description="当前价格")
    change: Optional[float] = Field(None, description="涨跌额")
    change_percent: Optional[float] = Field(None, description="涨跌幅 (%)")
    open: Optional[float] = Field(None, description="开盘价")
    high: Optional[float] = Field(None, description="最高价")
    low: Optional[float] = Field(None, description="最低价")
    prev_close: Optional[float] = Field(None, description="昨收价")
    volume: Optional[float] = Field(None, description="成交量（股）")
    amount: Optional[float] = Field(None, description="成交额（元）")
    update_time: Optional[str] = Field(None, description="更新时间")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "stock_code": "600519",
            "stock_name": "贵州茅台",
            "current_price": 1800.00,
            "change": 15.00,
            "change_percent": 0.84,
            "open": 1785.00,
            "high": 1810.00,
            "low": 1780.00,
            "prev_close": 1785.00,
            "volume": 10000000,
            "amount": 18000000000,
            "update_time": "2024-01-01T15:00:00"
        }
    })


class KLineData(BaseModel):
    """K 线数据点"""
    
    date: str = Field(..., description="日期")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: Optional[float] = Field(None, description="成交量")
    amount: Optional[float] = Field(None, description="成交额")
    change_percent: Optional[float] = Field(None, description="涨跌幅 (%)")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "date": "2024-01-01",
            "open": 1785.00,
            "high": 1810.00,
            "low": 1780.00,
            "close": 1800.00,
            "volume": 10000000,
            "amount": 18000000000,
            "change_percent": 0.84
        }
    })


class ExtractItem(BaseModel):
    """单条提取结果（代码、名称、置信度）"""

    code: Optional[str] = Field(None, description="股票代码，None 表示解析失败")
    name: Optional[str] = Field(None, description="股票名称（如有）")
    confidence: str = Field("medium", description="置信度：high/medium/low")


class ExtractFromImageResponse(BaseModel):
    """图片股票代码提取响应"""

    codes: List[str] = Field(..., description="提取的股票代码（已去重，向后兼容）")
    items: List[ExtractItem] = Field(default_factory=list, description="提取结果明细（代码+名称+置信度）")
    raw_text: Optional[str] = Field(None, description="原始 LLM 响应（调试用）")


class StockHistoryResponse(BaseModel):
    """股票历史行情响应"""

    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    period: str = Field(..., description="K 线周期")
    data: List[KLineData] = Field(default_factory=list, description="K 线数据列表")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "stock_code": "600519",
            "stock_name": "贵州茅台",
            "period": "daily",
            "data": []
        }
    })


class BatchQuoteItem(BaseModel):
    """批量行情响应项（精简版）"""

    code: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    current_price: Optional[float] = Field(None, description="当前价格")
    change_pct: Optional[float] = Field(None, description="涨跌幅 (%)")
    quote_time: Optional[str] = Field(None, description="行情时间")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "code": "600519",
            "name": "贵州茅台",
            "current_price": 1800.00,
            "change_pct": 0.84,
            "quote_time": "2026-06-22T14:30:00",
        }
    })


class PoolOverviewStockItem(BaseModel):
    """股池总览中的单个股票项"""

    code: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    current_price: Optional[float] = Field(None, description="当前价格")
    change_pct: Optional[float] = Field(None, description="涨跌幅 (%)")
    quote_time: Optional[str] = Field(None, description="行情时间")
    analysis_summary: Optional[str] = Field(None, description="分析摘要")
    action_label: Optional[str] = Field(None, description="建议动作标签")
    ideal_buy: Optional[float] = Field(None, description="理想买入价")
    stop_loss: Optional[float] = Field(None, description="止损价")
    take_profit: Optional[float] = Field(None, description="止盈价")


class PoolOverviewPoolItem(BaseModel):
    """股池总览中的单个股池项"""

    name: str = Field(..., description="股池名称")
    description: Optional[str] = Field(None, description="股池描述")
    updated_at: Optional[str] = Field(None, description="更新时间")
    stocks: List[PoolOverviewStockItem] = Field(default_factory=list, description="股票列表")
