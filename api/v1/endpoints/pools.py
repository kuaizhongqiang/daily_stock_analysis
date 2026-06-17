# -*- coding: utf-8 -*-
"""
===================================
股池管理 API 端点
===================================

职责：
1. 股池 CRUD
2. 股池成员管理
"""

import logging
from typing import Optional

from fastapi import APIRouter

from src.services.stock_pool_service import StockPoolService

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_pool_service() -> StockPoolService:
    return StockPoolService()


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
