# -*- coding: utf-8 -*-
"""
===================================
股池数据访问层
===================================

职责：
1. 封装股池（StockPool + StockPoolMember）的数据库操作
2. 提供 CRUD 接口
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import and_, func, select, delete

from src.storage import DatabaseManager, StockPool, StockPoolMember

logger = logging.getLogger(__name__)


class StockPoolRepository:
    """
    股池数据访问层

    封装 StockPool + StockPoolMember 表的数据库操作
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager.get_instance()

    # ---- Pool CRUD ----

    def create_pool(self, name: str, description: str = "", tags: str = "") -> Optional[Dict[str, Any]]:
        """创建一个新的股池，返回字典或 None（重复名称）。"""
        try:

            def _create(session):
                existing = session.execute(
                    select(StockPool).where(StockPool.name == name)
                ).scalar_one_or_none()
                if existing:
                    return None
                pool = StockPool(name=name, description=description, tags=tags)
                session.add(pool)
                session.flush()
                return {
                    "id": pool.id,
                    "name": pool.name,
                    "description": pool.description,
                    "tags": pool.tags,
                    "is_active": pool.is_active,
                    "created_at": pool.created_at.isoformat() if pool.created_at else None,
                    "updated_at": pool.updated_at.isoformat() if pool.updated_at else None,
                }

            return self.db._run_write_transaction("create_pool", _create)
        except Exception as e:
            logger.error(f"创建股池失败: {e}")
            return None

    def get_pool(self, pool_id: int) -> Optional[StockPool]:
        """按 ID 获取股池。"""
        try:
            with self.db.get_session() as session:
                return session.get(StockPool, pool_id)
        except Exception as e:
            logger.error(f"获取股池失败: {e}")
            return None

    def get_pool_by_name(self, name: str) -> Optional[StockPool]:
        """按名称获取股池。"""
        try:
            with self.db.get_session() as session:
                return session.execute(
                    select(StockPool).where(StockPool.name == name)
                ).scalar_one_or_none()
        except Exception as e:
            logger.error(f"按名称获取股池失败: {e}")
            return None

    def list_pools(self, active_only: bool = True) -> List[StockPool]:
        """列出股池。"""
        try:
            with self.db.get_session() as session:
                query = select(StockPool)
                if active_only:
                    query = query.where(StockPool.is_active.is_(True))
                query = query.order_by(StockPool.created_at.desc())
                return list(session.execute(query).scalars().all())
        except Exception as e:
            logger.error(f"列出股池失败: {e}")
            return []

    def update_pool(self, pool_id: int, **kwargs) -> bool:
        """更新股池属性（name, description, tags, is_active）。"""
        try:

            def _update(session):
                pool = session.get(StockPool, pool_id)
                if not pool:
                    return False
                for key, value in kwargs.items():
                    if hasattr(pool, key):
                        setattr(pool, key, value)
                pool.updated_at = datetime.now()
                return True

            return self.db._run_write_transaction("update_pool", _update)
        except Exception as e:
            logger.error(f"更新股池失败: {e}")
            return False

    def delete_pool(self, pool_id: int) -> bool:
        """删除股池（级联删除成员）。"""
        try:

            def _delete(session):
                pool = session.get(StockPool, pool_id)
                if not pool:
                    return False
                session.delete(pool)
                return True

            return self.db._run_write_transaction("delete_pool", _delete)
        except Exception as e:
            logger.error(f"删除股池失败: {e}")
            return False

    # ---- Pool Members ----

    def add_stock(self, pool_id: int, code: str, market: str = "cn",
                  reason: str = "", added_by: str = "manual") -> bool:
        """向股池添加一只股票。"""
        try:

            def _add(session):
                pool = session.get(StockPool, pool_id)
                if not pool:
                    return False
                existing = session.execute(
                    select(StockPoolMember).where(
                        and_(StockPoolMember.pool_id == pool_id,
                             StockPoolMember.code == code)
                    )
                ).scalar_one_or_none()
                if existing:
                    return True  # already exists, idempotent
                member = StockPoolMember(
                    pool_id=pool_id, code=code, market=market,
                    added_reason=reason, added_by=added_by,
                )
                session.add(member)
                return True

            return self.db._run_write_transaction("add_stock_to_pool", _add)
        except Exception as e:
            logger.error(f"添加股票到股池失败: {e}")
            return False

    def remove_stock(self, pool_id: int, code: str) -> bool:
        """从股池移除一只股票。"""
        try:

            def _remove(session):
                result = session.execute(
                    delete(StockPoolMember).where(
                        and_(StockPoolMember.pool_id == pool_id,
                             StockPoolMember.code == code)
                    )
                )
                return result.rowcount > 0

            return self.db._run_write_transaction("remove_stock_from_pool", _remove)
        except Exception as e:
            logger.error(f"从股池移除股票失败: {e}")
            return False

    def list_stocks(self, pool_id: int) -> List[StockPoolMember]:
        """列出股池内的所有股票。"""
        try:
            with self.db.get_session() as session:
                rows = session.execute(
                    select(StockPoolMember)
                    .where(StockPoolMember.pool_id == pool_id)
                    .order_by(StockPoolMember.created_at.desc())
                ).scalars().all()
                return list(rows)
        except Exception as e:
            logger.error(f"列出股池股票失败: {e}")
            return []

    def get_pools_for_stock(self, code: str) -> List[StockPool]:
        """获取包含某只股票的所有股池。"""
        try:
            with self.db.get_session() as session:
                rows = session.execute(
                    select(StockPool)
                    .join(StockPoolMember, StockPool.id == StockPoolMember.pool_id)
                    .where(StockPoolMember.code == code)
                ).scalars().all()
                return list(rows)
        except Exception as e:
            logger.error(f"获取股票所属股池失败: {e}")
            return []

    def get_member_count(self, pool_id: int) -> int:
        """获取单个股池的成员数量。"""
        try:
            with self.db.get_session() as session:
                return session.execute(
                    select(func.count(StockPoolMember.id))
                    .where(StockPoolMember.pool_id == pool_id)
                ).scalar() or 0
        except Exception as e:
            logger.error(f"获取成员数量失败: {e}")
            return 0

    def get_member_counts(self, pool_ids: List[int]) -> Dict[int, int]:
        """批量获取多个股池的成员数量（避免 N+1 查询）。"""
        if not pool_ids:
            return {}
        try:
            with self.db.get_session() as session:
                rows = session.execute(
                    select(StockPoolMember.pool_id, func.count(StockPoolMember.id))
                    .where(StockPoolMember.pool_id.in_(pool_ids))
                    .group_by(StockPoolMember.pool_id)
                ).all()
                return {row[0]: row[1] for row in rows}
        except Exception as e:
            logger.error(f"批量获取成员数量失败: {e}")
            return {}
