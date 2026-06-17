# -*- coding: utf-8 -*-
"""
===================================
向量索引元数据数据访问层
===================================

职责：
1. 封装 VectorIndexEntry 表的数据库操作
2. 提供索引状态查询与管理
"""

import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, func, and_, delete

from src.storage import DatabaseManager, VectorIndexEntry

logger = logging.getLogger(__name__)


class VectorIndexRepository:
    """
    向量索引元数据数据访问层
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager.get_instance()

    def record_indexed(self, doc_type: str, doc_id: int, source_table: str,
                       content_hash: str, chunk_index: int, chunk_text: str) -> bool:
        """记录一条已索引的文档块。"""
        try:

            def _record(session):
                entry = VectorIndexEntry(
                    doc_type=doc_type,
                    doc_id=doc_id,
                    source_table=source_table,
                    content_hash=content_hash,
                    chunk_index=chunk_index,
                    chunk_text=chunk_text,
                )
                session.add(entry)
                return True

            return self.db._run_write_transaction("record_vector_index", _record)
        except Exception as e:
            logger.error(f"记录向量索引元数据失败: {e}")
            return False

    def has_entry(self, doc_type: str, doc_id: int) -> bool:
        """检查文档是否已被索引。"""
        try:
            with self.db.get_session() as session:
                count = session.execute(
                    select(func.count(VectorIndexEntry.id))
                    .where(and_(
                        VectorIndexEntry.doc_type == doc_type,
                        VectorIndexEntry.doc_id == doc_id,
                    ))
                ).scalar() or 0
                return count > 0
        except Exception as e:
            logger.error(f"检查向量索引条目失败: {e}")
            return False

    def delete_entry(self, doc_type: str, doc_id: int) -> bool:
        """删除某个文档的所有索引条目。"""
        try:

            def _delete(session):
                session.execute(
                    delete(VectorIndexEntry).where(and_(
                        VectorIndexEntry.doc_type == doc_type,
                        VectorIndexEntry.doc_id == doc_id,
                    ))
                )
                return True

            return self.db._run_write_transaction("delete_vector_index", _delete)
        except Exception as e:
            logger.error(f"删除向量索引条目失败: {e}")
            return False

    def count_by_type(self) -> dict:
        """按文档类型统计索引数量。"""
        try:
            with self.db.get_session() as session:
                rows = session.execute(
                    select(VectorIndexEntry.doc_type, func.count(VectorIndexEntry.id))
                    .group_by(VectorIndexEntry.doc_type)
                ).all()
                return {row[0]: row[1] for row in rows}
        except Exception as e:
            logger.error(f"统计向量索引失败: {e}")
            return {}

    def get_recent(self, limit: int = 50) -> List[VectorIndexEntry]:
        """获取最近索引的条目。"""
        try:
            with self.db.get_session() as session:
                rows = session.execute(
                    select(VectorIndexEntry)
                    .order_by(VectorIndexEntry.indexed_at.desc())
                    .limit(limit)
                ).scalars().all()
                return list(rows)
        except Exception as e:
            logger.error(f"获取最近向量索引条目失败: {e}")
            return []
