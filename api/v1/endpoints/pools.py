# -*- coding: utf-8 -*-
"""
===================================
股池管理 API 端点
===================================

职责：
1. 股池 CRUD
2. 股池成员管理
3. 股池总览（含行情+分析摘要）
"""

import logging
from typing import Optional, List

from fastapi import APIRouter

from api.v1.schemas.stocks import PoolOverviewStockItem, PoolOverviewPoolItem
from src.repositories.analysis_repo import AnalysisRepository
from src.services.stock_pool_service import StockPoolService
from src.services.stock_service import StockService

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_pool_service() -> StockPoolService:
    return StockPoolService()


@router.get("/overview", response_model=List[PoolOverviewPoolItem])
async def pool_overview():
    """股池总览：返回所有活跃股池及其包含的股票实时行情和分析摘要。"""
    pool_service = _get_pool_service()
    stock_service = StockService()
    analysis_repo = AnalysisRepository()

    pools = pool_service.list_pools(active_only=True)
    result: List[PoolOverviewPoolItem] = []

    for pool in pools:
        pool_id = pool["id"]
        members = pool_service.list_stocks(pool_id)
        stock_items: List[PoolOverviewStockItem] = []

        for m in members:
            code = m["code"]
            # 获取实时行情
            quote = None
            try:
                quote = stock_service.get_realtime_quote(code)
            except Exception as e:
                logger.warning("获取 %s 行情失败: %s", code, e)

            # 获取最新分析摘要
            summary = None
            action_label = None
            ideal_buy = None
            stop_loss = None
            take_profit = None
            try:
                records = analysis_repo.get_list(code=code, days=30, limit=1)
                if records:
                    record = records[0]
                    summary = getattr(record, "analysis_summary", None)

                    # 从 raw_result JSON 中提取 action_label
                    raw = getattr(record, "raw_result", None)
                    if isinstance(raw, dict):
                        action_label = raw.get("action_label") or raw.get("action")
                    elif isinstance(raw, str):
                        import json
                        try:
                            raw_dict = json.loads(raw)
                            action_label = raw_dict.get("action_label") or raw_dict.get("action")
                        except (json.JSONDecodeError, TypeError):
                            pass

                    ideal_buy = getattr(record, "ideal_buy", None)
                    stop_loss = getattr(record, "stop_loss", None)
                    take_profit = getattr(record, "take_profit", None)
            except Exception as e:
                logger.warning("获取 %s 分析摘要失败: %s", code, e)

            quote_time = quote.get("update_time") if quote else None
            stock_items.append(PoolOverviewStockItem(
                code=code,
                name=m.get("name"),
                current_price=quote.get("current_price") if quote else None,
                change_pct=quote.get("change_percent") if quote else None,
                quote_time=quote_time,
                analysis_summary=summary,
                action_label=action_label,
                ideal_buy=ideal_buy,
                stop_loss=stop_loss,
                take_profit=take_profit,
            ))

        result.append(PoolOverviewPoolItem(
            name=pool["name"],
            description=pool.get("description"),
            updated_at=pool.get("updated_at"),
            stocks=stock_items,
        ))

    return result


@router.get("")
async def list_pools(active_only: bool = True):
    """列出所有股池。"""
    service = _get_pool_service()
    pools = service.list_pools(active_only=active_only)
    return {"pools": pools, "count": len(pools)}


@router.post("")
async def create_pool(name: str, description: str = "", tags: str = ""):
    """创建股池。"""
    service = _get_pool_service()
    pool = service.create_pool(name, description, tags)
    if pool is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail=f"Pool '{name}' already exists")
    return {"pool": pool, "status": "created"}


@router.get("/{pool_id}")
async def get_pool(pool_id: int):
    """获取股池详情。"""
    service = _get_pool_service()
    pool = service.get_pool(pool_id)
    if pool is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pool not found")
    return {"pool": pool}


@router.put("/{pool_id}")
async def update_pool(pool_id: int, name: Optional[str] = None,
                      description: Optional[str] = None,
                      tags: Optional[str] = None,
                      is_active: Optional[bool] = None):
    """更新股池属性。"""
    service = _get_pool_service()
    kwargs = {}
    if name is not None:
        kwargs["name"] = name
    if description is not None:
        kwargs["description"] = description
    if tags is not None:
        kwargs["tags"] = tags
    if is_active is not None:
        kwargs["is_active"] = is_active
    success = service.update_pool(pool_id, **kwargs)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pool not found")
    return {"status": "updated"}


@router.delete("/{pool_id}")
async def delete_pool(pool_id: int):
    """删除股池。"""
    service = _get_pool_service()
    success = service.delete_pool(pool_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pool not found")
    return {"status": "deleted", "pool_id": pool_id}


@router.post("/{pool_id}/stocks")
async def add_stock(pool_id: int, code: str, market: str = "cn", reason: str = ""):
    """向股池添加股票。"""
    service = _get_pool_service()
    success = service.add_stock(pool_id, code, market, reason)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Failed to add {code} to pool {pool_id}")
    return {"status": "added", "pool_id": pool_id, "code": code}


@router.delete("/{pool_id}/stocks")
async def remove_stock(pool_id: int, code: str):
    """从股池移除股票。"""
    service = _get_pool_service()
    success = service.remove_stock(pool_id, code)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Failed to remove {code} from pool {pool_id}")
    return {"status": "removed", "pool_id": pool_id, "code": code}


@router.get("/{pool_id}/stocks")
async def list_stocks(pool_id: int):
    """列出股池内股票。"""
    service = _get_pool_service()
    stocks = service.list_stocks(pool_id)
    return {"pool_id": pool_id, "stocks": stocks, "count": len(stocks)}
