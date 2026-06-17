# -*- coding: utf-8 -*-
"""
===================================
向量搜索 API 端点
===================================
"""

import logging
from typing import Optional

from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/semantic")
async def semantic_search(
    query: str = Query(..., description="Search query"),
    doc_type: Optional[str] = Query(None, description="Document type filter"),
    limit: int = Query(10, description="Max results"),
    threshold: float = Query(0.0, description="Minimum similarity threshold"),
):
    """语义搜索。"""
    try:
        from src.services.vector_search_service import VectorSearchService
        svc = VectorSearchService()
        results = svc.search(query, doc_type=doc_type, top_k=limit, threshold=threshold)
        return {
            "query": query,
            "results": [
                {
                    "doc_type": r.doc_type,
                    "doc_id": r.doc_id,
                    "chunk_index": r.chunk_index,
                    "text": r.text[:500],
                    "score": r.score,
                    "source_table": r.source_table,
                }
                for r in results
            ],
            "count": len(results),
        }
    except Exception as e:
        from fastapi import HTTPException
        logger.error("Vector search failed: %s", e)
        raise HTTPException(status_code=500, detail="Search service unavailable")


@router.post("/index")
async def trigger_index(doc_type: Optional[str] = None):
    """触发索引重建（基于已有元数据）。"""
    try:
        from src.services.vector_search_service import VectorSearchService
        svc = VectorSearchService()
        types = [doc_type] if doc_type else None
        result = svc.rebuild_index(doc_types=types)
        return result
    except Exception as e:
        from fastapi import HTTPException
        logger.error("Index rebuild failed: %s", e)
        raise HTTPException(status_code=500, detail="Index service unavailable")


@router.get("/status")
async def index_status():
    """获取索引状态。"""
    try:
        from src.services.vector_search_service import VectorSearchService
        svc = VectorSearchService()
        return svc.index_status()
    except Exception as e:
        from fastapi import HTTPException
        logger.error("Index status failed: %s", e)
        raise HTTPException(status_code=500, detail="Status service unavailable")
