# -*- coding: utf-8 -*-
"""
CLI vector commands — semantic search and index management.
"""
from __future__ import annotations

import click

from dsa.output import JsonOutput, pass_json


@click.group(name="vector")
def vector() -> None:
    """Semantic search and vector index management."""


@vector.command(name="search")
@click.argument("query")
@click.option("--type", "-t", "doc_type", default=None, help="Document type filter (analysis, news, conversation)")
@click.option("--limit", "-l", default=10, type=int, help="Max results")
@click.option("--threshold", default=0.0, type=float, help="Minimum similarity threshold (0-1)")
@pass_json
def vector_search(json_out: JsonOutput, query: str, doc_type: str | None, limit: int, threshold: float) -> None:
    """Semantic search across indexed content."""
    try:
        from src.services.vector_search_service import VectorSearchService
        svc = VectorSearchService()
        results = svc.search(query, doc_type=doc_type, top_k=limit, threshold=threshold)
        json_out.ok({
            "query": query,
            "results": [
                {
                    "doc_type": r.doc_type,
                    "doc_id": r.doc_id,
                    "text": r.text[:200],
                    "score": r.score,
                    "source_table": r.source_table,
                }
                for r in results
            ],
            "count": len(results),
        })
    except Exception as e:
        json_out.error("VECTOR_SEARCH_ERROR", str(e))


@vector.command(name="index")
@click.option("--reindex", is_flag=True, help="Rebuild all vector indexes from metadata")
@click.option("--type", "-t", "doc_type", default=None, help="Only rebuild specific doc type")
@pass_json
def vector_index(json_out: JsonOutput, reindex: bool, doc_type: str | None) -> None:
    """Manage vector index."""
    try:
        from src.services.vector_search_service import VectorSearchService
        svc = VectorSearchService()

        if reindex:
            types = [doc_type] if doc_type else None
            result = svc.rebuild_index(doc_types=types)
            json_out.ok(result)
        else:
            status = svc.index_status()
            json_out.ok(status)
    except Exception as e:
        json_out.error("VECTOR_INDEX_ERROR", str(e))


@vector.command(name="status")
@pass_json
def vector_status(json_out: JsonOutput) -> None:
    """Show vector index status."""
    try:
        from src.services.vector_search_service import VectorSearchService
        svc = VectorSearchService()
        status = svc.index_status()
        json_out.ok(status)
    except Exception as e:
        json_out.error("VECTOR_STATUS_ERROR", str(e))


if __name__ == "__main__":
    vector()
