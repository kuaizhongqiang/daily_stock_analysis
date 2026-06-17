# -*- coding: utf-8 -*-
"""Tests for VectorSearchService (chunking logic only, LM Studio not required)."""
from src.services.vector_search_service import VectorSearchService


class TestVectorSearchChunking:
    """Vector search chunking tests (no LM Studio needed)."""

    def setup_method(self):
        self.svc = VectorSearchService()

    def test_chunk_short_text(self):
        text = "贵州茅台今日股价上涨。"
        chunks = self.svc.chunk_text(text, "analysis", 1, "analysis_history")
        assert len(chunks) == 1
        assert chunks[0].doc_type == "analysis"
        assert chunks[0].doc_id == 1
        assert chunks[0].text == text

    def test_chunk_empty_text(self):
        chunks = self.svc.chunk_text("", "analysis", 1, "")
        assert len(chunks) == 0

    def test_chunk_multiple_sentences(self):
        text = "第一句话。第二句话！第三句话？第四句话。"
        chunks = self.svc.chunk_text(text, "news", 1, "news_intel")
        assert len(chunks) >= 1
        assert chunks[0].doc_type == "news"

    def test_index_status_no_data(self):
        status = self.svc.index_status()
        assert "total_chunks" in status
        assert "by_doc_type" in status
        assert "deleted_chunks" in status
        assert "active_chunks" in status


class TestVectorSearchMetadata:
    """Metadata and soft-delete tests (no LM Studio needed)."""

    def setup_method(self):
        self.svc = VectorSearchService()

    def test_soft_delete(self):
        """软删除应在元数据中标记 deleted=True 而不移除条目。"""
        from src.services.vector_search_service import VECTOR_DATA_DIR
        import os, shutil

        # Clean slate
        if VECTOR_DATA_DIR.exists():
            shutil.rmtree(VECTOR_DATA_DIR)

        # Manually inject metadata to simulate an indexed doc
        meta = {
            "analysis:42:0": {
                "doc_type": "analysis", "doc_id": 42, "chunk_index": 0,
                "text": "测试文本", "source_table": "test",
                "deleted": False,  # active
            },
            "analysis:99:0": {
                "doc_type": "analysis", "doc_id": 99, "chunk_index": 0,
                "text": "另一条", "source_table": "test",
                "deleted": False,
            },
        }
        from src.services.vector_search_service import VectorSearchService
        svc = VectorSearchService()
        svc._save_metadata(meta)

        # Delete document 42
        ok = svc.delete_document("analysis", 42)
        assert ok, "delete_document failed"

        # Check metadata: doc 42 should be marked deleted, doc 99 unchanged
        updated = svc._load_metadata()
        assert updated["analysis:42:0"]["deleted"] is True
        assert updated["analysis:99:0"].get("deleted", False) is False

        # Cleanup
        if VECTOR_DATA_DIR.exists():
            shutil.rmtree(VECTOR_DATA_DIR)

    def test_delete_nonexistent(self):
        """删除不存在的文档应返回 True（幂等）。"""
        ok = self.svc.delete_document("nonexistent", 999)
        assert ok is True

    def test_remote_mode_requires_url(self):
        """remote 模式未设置 EMBEDDING_BASE_URL 应报错。"""
        import os
        original = os.environ.get("EMBEDDING_PROVIDER")
        original_url = os.environ.get("EMBEDDING_BASE_URL")
        try:
            os.environ["EMBEDDING_PROVIDER"] = "remote"
            if "EMBEDDING_BASE_URL" in os.environ:
                del os.environ["EMBEDDING_BASE_URL"]
            # Reset singleton
            from src.embedding_service import EmbeddingService
            EmbeddingService._instance = None
            try:
                EmbeddingService()
                assert False, "应该抛出 ValueError"
            except ValueError as e:
                assert "EMBEDDING_BASE_URL" in str(e)
        finally:
            if original:
                os.environ["EMBEDDING_PROVIDER"] = original
            else:
                os.environ.pop("EMBEDDING_PROVIDER", None)
            if original_url:
                os.environ["EMBEDDING_BASE_URL"] = original_url

    def test_status_counts_deleted(self):
        """index_status 应正确区分 active/deleted。"""
        from src.services.vector_search_service import VECTOR_DATA_DIR
        import shutil

        if VECTOR_DATA_DIR.exists():
            shutil.rmtree(VECTOR_DATA_DIR)

        meta = {
            "a:1:0": {"doc_type": "a", "text": "x", "deleted": False},
            "a:2:0": {"doc_type": "a", "text": "y", "deleted": True},
        }
        svc = VectorSearchService()
        svc._save_metadata(meta)

        status = svc.index_status()
        assert status["total_chunks"] == 2
        assert status["deleted_chunks"] == 1
        assert status["active_chunks"] == 1

        if VECTOR_DATA_DIR.exists():
            shutil.rmtree(VECTOR_DATA_DIR)
