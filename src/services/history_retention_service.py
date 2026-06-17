# -*- coding: utf-8 -*-
"""
===================================
历史消息留存服务
===================================

职责：
1. 分析会话管理（列表、查询）
2. 跨引用分析历史 ↔ 对话
3. 历史导出（JSON/CSV）
4. 历史清理策略（按天数/数量/标签）
"""

import csv
import io
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, desc, func, or_, select

from src.storage import (
    AnalysisHistory,
    AnalysisSession,
    ConversationMessage,
    DatabaseManager,
)

logger = logging.getLogger(__name__)


class HistoryRetentionService:
    """历史消息留存服务。"""

    def __init__(self):
        self.db = DatabaseManager.get_instance()

    # -----------------------------------------------------------------------
    # 会话管理
    # -----------------------------------------------------------------------

    def list_sessions(self, days: int = 30, limit: int = 50) -> List[Dict[str, Any]]:
        """列出最近的分析会话。"""
        cutoff = datetime.now() - timedelta(days=days)
        try:
            with self.db.get_session() as session:
                rows = session.execute(
                    select(AnalysisSession)
                    .where(AnalysisSession.started_at >= cutoff)
                    .order_by(desc(AnalysisSession.started_at))
                    .limit(limit)
                ).scalars().all()
                return [
                    {
                        "id": s.id,
                        "session_id": s.session_id,
                        "title": s.title,
                        "conversation_session_id": s.conversation_session_id,
                        "message_count": s.message_count,
                        "token_count": s.token_count,
                        "tags": s.tags,
                        "started_at": s.started_at.isoformat() if s.started_at else None,
                        "ended_at": s.ended_at.isoformat() if s.ended_at else None,
                    }
                    for s in rows
                ]
        except Exception as e:
            logger.error("[HistoryRetention] 列出会话失败: %s", e)
            return []

    def get_session_analyses(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会分析话关联的所有分析历史。"""
        try:
            with self.db.get_session() as db_session:
                rows = db_session.execute(
                    select(AnalysisHistory)
                    .where(AnalysisHistory.conversation_session_id == session_id)
                    .order_by(desc(AnalysisHistory.created_at))
                ).scalars().all()
                return [
                    {
                        "id": a.id,
                        "code": a.code,
                        "name": a.name,
                        "sentiment_score": a.sentiment_score,
                        "operation_advice": a.operation_advice,
                        "trend_prediction": a.trend_prediction,
                        "analysis_summary": a.analysis_summary[:200] if a.analysis_summary else "",
                        "created_at": a.created_at.isoformat() if a.created_at else None,
                    }
                    for a in rows
                ]
        except Exception as e:
            logger.error("[HistoryRetention] 获取会话分析失败: %s", e)
            return []

    # -----------------------------------------------------------------------
    # 历史搜索
    # -----------------------------------------------------------------------

    def search_history(self, query: str, days: int = 90, limit: int = 20) -> List[Dict[str, Any]]:
        """全文搜索分析历史（按关键词匹配摘要/结论）。"""
        try:
            with self.db.get_session() as db_session:
                keyword = f"%{query}%"
                rows = db_session.execute(
                    select(AnalysisHistory)
                    .where(and_(
                        AnalysisHistory.created_at >= (datetime.now() - timedelta(days=days)),
                        or_(
                            AnalysisHistory.analysis_summary.ilike(keyword),
                            AnalysisHistory.operation_advice.ilike(keyword),
                            AnalysisHistory.trend_prediction.ilike(keyword),
                            AnalysisHistory.code.ilike(keyword),
                            AnalysisHistory.name.ilike(keyword),
                        ),
                    ))
                    .order_by(desc(AnalysisHistory.created_at))
                    .limit(limit)
                ).scalars().all()
                return [
                    {
                        "id": a.id,
                        "code": a.code,
                        "name": a.name,
                        "sentiment_score": a.sentiment_score,
                        "operation_advice": a.operation_advice,
                        "trend_prediction": a.trend_prediction,
                        "analysis_summary": a.analysis_summary[:300] if a.analysis_summary else "",
                        "created_at": a.created_at.isoformat() if a.created_at else None,
                    }
                    for a in rows
                ]
        except Exception as e:
            logger.error("[HistoryRetention] 搜索历史失败: %s", e)
            return []

    def search_conversations(self, query: str, days: int = 30, limit: int = 20) -> List[Dict[str, Any]]:
        """全文搜索对话消息。"""
        try:
            with self.db.get_session() as db_session:
                keyword = f"%{query}%"
                rows = db_session.execute(
                    select(ConversationMessage)
                    .where(and_(
                        ConversationMessage.created_at >= (datetime.now() - timedelta(days=days)),
                        ConversationMessage.content.ilike(keyword),
                    ))
                    .order_by(desc(ConversationMessage.created_at))
                    .limit(limit)
                ).scalars().all()
                return [
                    {
                        "id": m.id,
                        "session_id": m.session_id,
                        "role": m.role,
                        "content": m.content[:300],
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                    }
                    for m in rows
                ]
        except Exception as e:
            logger.error("[HistoryRetention] 搜索对话失败: %s", e)
            return []

    # -----------------------------------------------------------------------
    # 历史导出
    # -----------------------------------------------------------------------

    def export_analysis_json(self, days: int = 30, code: Optional[str] = None) -> str:
        """导出分析历史为 JSON 字符串。"""
        try:
            with self.db.get_session() as db_session:
                query = select(AnalysisHistory).where(
                    AnalysisHistory.created_at >= (datetime.now() - timedelta(days=days))
                )
                if code:
                    query = query.where(AnalysisHistory.code == code)
                query = query.order_by(desc(AnalysisHistory.created_at))

                rows = db_session.execute(query).scalars().all()
                records = [
                    {
                        "id": r.id,
                        "code": r.code,
                        "name": r.name,
                        "report_type": r.report_type,
                        "sentiment_score": r.sentiment_score,
                        "operation_advice": r.operation_advice,
                        "trend_prediction": r.trend_prediction,
                        "analysis_summary": r.analysis_summary,
                        "ideal_buy": r.ideal_buy,
                        "secondary_buy": r.secondary_buy,
                        "stop_loss": r.stop_loss,
                        "take_profit": r.take_profit,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                    }
                    for r in rows
                ]
                return json.dumps(records, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("[HistoryRetention] 导出分析历史失败: %s", e)
            return json.dumps([])

    def export_analysis_csv(self, days: int = 30, code: Optional[str] = None) -> str:
        """导出分析历史为 CSV 字符串。"""
        try:
            with self.db.get_session() as db_session:
                query = select(AnalysisHistory).where(
                    AnalysisHistory.created_at >= (datetime.now() - timedelta(days=days))
                )
                if code:
                    query = query.where(AnalysisHistory.code == code)
                query = query.order_by(desc(AnalysisHistory.created_at))

                rows = db_session.execute(query).scalars().all()
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow([
                    "id", "code", "name", "report_type",
                    "sentiment_score", "operation_advice", "trend_prediction",
                    "analysis_summary", "ideal_buy", "stop_loss", "take_profit",
                    "created_at",
                ])
                for r in rows:
                    writer.writerow([
                        r.id, r.code, r.name, r.report_type,
                        r.sentiment_score, r.operation_advice, r.trend_prediction,
                        r.analysis_summary, r.ideal_buy, r.stop_loss, r.take_profit,
                        r.created_at.isoformat() if r.created_at else "",
                    ])
                return output.getvalue()
        except Exception as e:
            logger.error("[HistoryRetention] 导出分析历史 CSV 失败: %s", e)
            return ""

    # -----------------------------------------------------------------------
    # 历史清理
    # -----------------------------------------------------------------------

    def prune_analysis(self, older_than_days: int = 90, code: Optional[str] = None) -> int:
        """清理指定天数之前的分析历史。

        Args:
            older_than_days: 保留多少天内的数据
            code: 可选，只清理特定股票

        Returns:
            删除的记录数
        """
        cutoff = datetime.now() - timedelta(days=older_than_days)
        try:

            def _prune(session):
                query = delete(AnalysisHistory).where(
                    AnalysisHistory.created_at < cutoff
                )
                if code:
                    query = query.where(AnalysisHistory.code == code)
                result = session.execute(query)
                return result.rowcount

            return self.db._run_write_transaction("prune_analysis", _prune)
        except Exception as e:
            logger.error("[HistoryRetention] 清理分析历史失败: %s", e)
            return 0

    def prune_conversations(self, older_than_days: int = 30, session_id: Optional[str] = None) -> int:
        """清理旧对话消息。"""
        cutoff = datetime.now() - timedelta(days=older_than_days)
        try:

            def _prune(session):
                query = delete(ConversationMessage).where(
                    ConversationMessage.created_at < cutoff
                )
                if session_id:
                    query = query.where(ConversationMessage.session_id == session_id)
                result = session.execute(query)
                return result.rowcount

            return self.db._run_write_transaction("prune_conversations", _prune)
        except Exception as e:
            logger.error("[HistoryRetention] 清理对话失败: %s", e)
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """获取历史数据统计。"""
        try:
            with self.db.get_session() as db_session:
                analysis_count = db_session.execute(
                    select(func.count(AnalysisHistory.id))
                ).scalar() or 0
                conversation_count = db_session.execute(
                    select(func.count(ConversationMessage.id))
                ).scalar() or 0
                session_count = db_session.execute(
                    select(func.count(AnalysisSession.id))
                ).scalar() or 0

                # 最早和最晚记录
                earliest = db_session.execute(
                    select(func.min(AnalysisHistory.created_at))
                ).scalar()
                latest = db_session.execute(
                    select(func.max(AnalysisHistory.created_at))
                ).scalar()

                return {
                    "analysis_count": analysis_count,
                    "conversation_count": conversation_count,
                    "session_count": session_count,
                    "earliest_analysis": earliest.isoformat() if earliest else None,
                    "latest_analysis": latest.isoformat() if latest else None,
                }
        except Exception as e:
            logger.error("[HistoryRetention] 获取统计失败: %s", e)
            return {}
