"""dsa session — 会话语境保持。

Usage:
    dsa session start                           创建新会话
    dsa session context <session_id>            查看会话上下文
    dsa session close <session_id>              关闭会话
    dsa session ls                              列出活跃会话
    dsa analyze <code> --session <session_id>   在会话下分析
"""
from __future__ import annotations

import click
from datetime import datetime

from ..output import JsonOutput, pass_json


@click.group(name="session")
def session() -> None:
    """会话语境保持与管理。"""


@session.command()
@pass_json
def start(json_out: JsonOutput) -> None:
    """创建新的分析会话，返回 session_id。"""
    import uuid
    from src.agent.conversation import conversation_manager

    session_id = str(uuid.uuid4())[:8]
    conversation_manager.get_or_create(session_id)
    json_out.ok({
        "session_id": session_id,
        "message": "Session created. Use `dsa analyze <code> --session <session_id>` to analyze under this session.",
    })


@session.command(name="context")
@click.argument("session_id")
@pass_json
def show_context(json_out: JsonOutput, session_id: str) -> None:
    """查看会话上下文：当前分析过的标的、活跃股池等。"""
    from src.agent.conversation import conversation_manager

    try:
        session = conversation_manager.get_or_create(session_id)
        history = session.get_history()
        json_out.ok({
            "session_id": session_id,
            "created_at": str(session.created_at),
            "last_active": str(session.last_active),
            "context": session.context,
            "message_count": len(history),
            "recent_messages": [
                {"role": m.get("role", ""), "content": (m.get("content", "") or "")[:200]}
                for m in history[-10:]
            ],
        })
    except Exception as e:
        json_out.error("SESSION_ERROR", str(e))


@session.command()
@click.argument("session_id")
@pass_json
def close(json_out: JsonOutput, session_id: str) -> None:
    """关闭并清理会话。"""
    from src.agent.conversation import conversation_manager

    try:
        conversation_manager.clear(session_id)
        json_out.ok({
            "session_id": session_id,
            "status": "closed",
            "message": "Session closed and context cleared.",
        })
    except Exception as e:
        json_out.error("SESSION_ERROR", str(e))


@session.command(name="ls")
@pass_json
def list_sessions(json_out: JsonOutput) -> None:
    """列出当前活跃会话。"""
    from src.agent.conversation import conversation_manager

    sessions = conversation_manager.list_active()
    json_out.ok({"sessions": sessions, "count": len(sessions)})
