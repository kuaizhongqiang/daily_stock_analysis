# -*- coding: utf-8 -*-
"""
===================================
通知工具函数
===================================

从已删除的 sender 模块中提取的公共 URL 解析函数。
"""

from __future__ import annotations

from typing import Optional, Tuple
from urllib.parse import unquote, urlparse, urlunparse


def resolve_ntfy_endpoint(ntfy_url: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Split NTFY_URL into server root and topic from the final path segment."""
    raw_url = (ntfy_url or "").strip().rstrip("/")
    if not raw_url:
        return None, None

    parsed = urlparse(raw_url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return None, None

    path_segments = [segment for segment in parsed.path.split("/") if segment]
    if not path_segments:
        return None, None

    topic = unquote(path_segments[-1]).strip()
    if not topic:
        return None, None

    root_path = "/".join(path_segments[:-1])
    server_url = urlunparse(
        parsed._replace(
            path=f"/{root_path}" if root_path else "",
            params="",
            query="",
            fragment="",
        )
    ).rstrip("/")

    return server_url, topic


def resolve_gotify_message_endpoint(gotify_url: Optional[str]) -> Optional[str]:
    """Resolve GOTIFY_URL server base into the fixed /message endpoint."""
    raw_url = (gotify_url or "").strip().rstrip("/")
    if not raw_url:
        return None

    parsed = urlparse(raw_url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return None
    if parsed.query or parsed.fragment:
        return None

    path_segments = [segment for segment in parsed.path.split("/") if segment]
    if path_segments and path_segments[-1].lower() == "message":
        return None

    base_url = urlunparse(
        parsed._replace(
            path="/" + "/".join(path_segments) if path_segments else "",
            params="",
            query="",
            fragment="",
        )
    ).rstrip("/")
    return f"{base_url}/message"
