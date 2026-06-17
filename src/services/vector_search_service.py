# -*- coding: utf-8 -*-
"""
===================================
向量搜索服务
===================================

职责：
1. 文档分块与索引
2. 语义搜索（本地/远程双模式）
3. 混合搜索（全文 + 语义）
4. 索引管理（增量/全量重建）

存储架构：
  - 使用 numpy .npy 文件存储向量：data/vectors/{doc_type}.npy
  - 使用 JSON 元数据文件跟踪索引内容：data/vectors/metadata.json
  - VectorIndexEntry 表记录索引元数据（可选冗余）

工作流：
  Index: 文档 → 分块 → embed → 追加到 .npy → 更新 metadata
  Search: query → embed → 加载 .npy → cosine sim → 排序 → 返回 Top-K
"""

import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from src.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

# 向量数据存储目录
VECTOR_DATA_DIR = Path(os.getenv("VECTOR_DATA_DIR", "./data/vectors"))
# 分块参数
CHUNK_SIZE = int(os.getenv("VECTOR_CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("VECTOR_CHUNK_OVERLAP", "64"))
# 搜索参数
DEFAULT_TOP_K = int(os.getenv("VECTOR_TOP_K", "10"))
# 相似度阈值
DEFAULT_SIMILARITY_THRESHOLD = float(os.getenv("VECTOR_SIMILARITY_THRESHOLD", "0.0"))


@dataclass
class ChunkRecord:
    """单个文档块的索引记录。"""
    id: str  # "{doc_type}:{doc_id}:{chunk_index}"
    doc_type: str
    doc_id: int
    source_table: str
    chunk_index: int
    text: str
    content_hash: str
    indexed_at: float  # timestamp


@dataclass
class SearchResult:
    """搜索结果条目。"""
    doc_type: str
    doc_id: int
    chunk_index: int
    text: str
    source_table: str
    score: float  # cosine similarity (0-1)


class VectorSearchService:
    """向量搜索服务。"""

    def __init__(self):
        self._embedding = EmbeddingService()
        self._dim = self._embedding.dimension
        self._lock = threading.Lock()
        VECTOR_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------------
    # 文档分块
    # -----------------------------------------------------------------------

    def chunk_text(self, text: str, doc_type: str, doc_id: int, source_table: str) -> List[ChunkRecord]:
        """将长文本分割为有重叠的块。"""
        if not text or not text.strip():
            return []

        # 尝试按句子边界分割
        import re
        sentences = re.split(r'(?<=[。！？.!?])\s*', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks: List[ChunkRecord] = []
        current_chunk = ""
        chunk_index = 0

        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= CHUNK_SIZE:
                current_chunk += sentence
            else:
                if current_chunk:
                    content_hash = hashlib.md5(current_chunk.encode("utf-8")).hexdigest()
                    chunks.append(ChunkRecord(
                        id=f"{doc_type}:{doc_id}:{chunk_index}",
                        doc_type=doc_type,
                        doc_id=doc_id,
                        source_table=source_table,
                        chunk_index=chunk_index,
                        text=current_chunk,
                        content_hash=content_hash,
                        indexed_at=time.time(),
                    ))
                    chunk_index += 1
                    # 重叠：保留部分内容
                    overlap = current_chunk[-CHUNK_OVERLAP:] if len(current_chunk) > CHUNK_OVERLAP else ""
                    current_chunk = overlap + sentence
                else:
                    current_chunk = sentence

        # 处理最后一个块
        if current_chunk:
            content_hash = hashlib.md5(current_chunk.encode("utf-8")).hexdigest()
            chunks.append(ChunkRecord(
                id=f"{doc_type}:{doc_id}:{chunk_index}",
                doc_type=doc_type,
                doc_id=doc_id,
                source_table=source_table,
                chunk_index=chunk_index,
                text=current_chunk,
                content_hash=content_hash,
                indexed_at=time.time(),
            ))

        return chunks

    # -----------------------------------------------------------------------
    # 文件级向量存储
    # -----------------------------------------------------------------------

    def _vectors_path(self, doc_type: str) -> Path:
        return VECTOR_DATA_DIR / f"{doc_type}.npy"

    def _metadata_path(self) -> Path:
        return VECTOR_DATA_DIR / "metadata.json"

    def _load_metadata(self) -> Dict[str, dict]:
        """加载全部索引元数据。"""
        path = self._metadata_path()
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("[VectorSearch] 元数据加载失败: %s", e)
        return {}

    def _save_metadata(self, metadata: Dict[str, dict]) -> None:
        """保存全部索引元数据。"""
        self._metadata_path().write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load_vectors(self, doc_type: str) -> np.ndarray:
        """加载某个类型的全部向量。"""
        path = self._vectors_path(doc_type)
        if path.exists():
            return np.load(path)
        return np.empty((0, self._dim), dtype=np.float32)

    def _save_vectors(self, doc_type: str, vectors: np.ndarray) -> None:
        """保存某个类型的全部向量。"""
        np.save(str(self._vectors_path(doc_type)), vectors)

    # -----------------------------------------------------------------------
    # 索引
    # -----------------------------------------------------------------------

    def index_document(self, doc_type: str, doc_id: int,
                       text: str, source_table: str = "") -> int:
        """索引单个文档。

        Args:
            doc_type: 文档类型 (analysis / news / conversation)
            doc_id: 源表记录 ID
            text: 文档文本内容
            source_table: 源表名（可选）

        Returns:
            索引的块数，0 表示失败或跳过
        """
        if not text or not text.strip():
            return 0

        # 分块
        chunks = self.chunk_text(text, doc_type, doc_id, source_table)
        if not chunks:
            return 0

        # 提取文本列表用于批量 embedding
        texts = [c.text for c in chunks]

        with self._lock:
            try:
                # 批量向量化
                vectors = self._embedding.embed(texts)
                vec_array = np.array(vectors, dtype=np.float32)
                # L2 归一化：确保余弦相似度 = dot product
                norms = np.linalg.norm(vec_array, axis=1, keepdims=True)
                norms = np.where(norms == 0, 1.0, norms)  # 避免除零
                vec_array = vec_array / norms

                # 加载现有向量并追加
                existing = self._load_vectors(doc_type)
                if len(existing) > 0:
                    new_vectors = np.vstack([existing, vec_array])
                else:
                    new_vectors = vec_array

                self._save_vectors(doc_type, new_vectors)

                # 更新元数据
                metadata = self._load_metadata()
                for chunk in chunks:
                    key = chunk.id
                    d = asdict(chunk)
                    metadata[key] = d

                self._save_metadata(metadata)

                logger.info("[VectorSearch] 索引完成: type=%s id=%d chunks=%d", doc_type, doc_id, len(chunks))
                return len(chunks)

            except Exception as e:
                logger.error("[VectorSearch] 索引失败: type=%s id=%d error=%s", doc_type, doc_id, e)
                return 0

    def delete_document(self, doc_type: str, doc_id: int) -> bool:
        """标记删除某个文档的所有索引条目（软删除，避免全量重嵌）。

        被标记删除的条目在搜索时会被过滤掉。
        如需物理清理，使用 rebuild_index 重建。
        """
        with self._lock:
            try:
                metadata = self._load_metadata()
                prefix = f"{doc_type}:{doc_id}:"
                keys = [k for k in metadata if k.startswith(prefix)]

                if not keys:
                    return True

                for key in keys:
                    metadata[key]["deleted"] = True
                self._save_metadata(metadata)

                logger.info("[VectorSearch] 标记删除: type=%s id=%d chunks=%d", doc_type, doc_id, len(keys))
                return True

            except Exception as e:
                logger.error("[VectorSearch] 删除索引失败: type=%s id=%d error=%s", doc_type, doc_id, e)
                return False

    # -----------------------------------------------------------------------
    # 搜索
    # -----------------------------------------------------------------------

    def search(self, query: str, doc_type: Optional[str] = None,
               top_k: int = DEFAULT_TOP_K,
               threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> List[SearchResult]:
        """语义搜索。

        Args:
            query: 查询文本
            doc_type: 可选的文档类型过滤
            top_k: 返回结果数
            threshold: 最低相似度阈值

        Returns:
            按相似度降序排列的搜索结果列表
        """
        if not query or not query.strip():
            return []

        with self._lock:
            try:
                # 向量化查询并 L2 归一化
                query_vec = self._embedding.embed_query(query)
                query_arr = np.array([query_vec], dtype=np.float32)
                q_norm = np.linalg.norm(query_arr)
                if q_norm > 0:
                    query_arr = query_arr / q_norm

                # 加载元数据
                metadata = self._load_metadata()

                # 确定搜索范围
                if doc_type:
                    types = [doc_type]
                else:
                    types = sorted(set(v["doc_type"] for v in metadata.values()))

                all_scores: List[tuple[float, str]] = []

                for dt in types:
                    vectors = self._load_vectors(dt)
                    if len(vectors) == 0:
                        continue

                    # 余弦相似度 (已归一化向量 => dot product = cosine)
                    scores = np.dot(vectors, query_arr.T).flatten()

                    # 找出该类型中未被删除的匹配索引
                    type_keys = [
                        k for k, v in metadata.items()
                        if v["doc_type"] == dt and not v.get("deleted", False)
                    ]
                    type_keys.sort(key=lambda k: metadata[k]["chunk_index"])

                    # 限制到有效的元数据数量
                    valid_count = min(len(type_keys), len(scores))
                    for i in range(valid_count):
                        score = float(scores[i])
                        if score >= threshold:
                            all_scores.append((score, type_keys[i]))

                # 按分数降序排列
                all_scores.sort(key=lambda x: x[0], reverse=True)

                # 取 Top-K
                results: List[SearchResult] = []
                for score, key in all_scores[:top_k]:
                    info = metadata.get(key, {})
                    results.append(SearchResult(
                        doc_type=info.get("doc_type", ""),
                        doc_id=info.get("doc_id", 0),
                        chunk_index=info.get("chunk_index", 0),
                        text=info.get("text", ""),
                        source_table=info.get("source_table", ""),
                        score=round(score, 4),
                    ))

                return results

            except Exception as e:
                logger.error("[VectorSearch] 搜索失败: query=%s error=%s", query[:50], e)
                return []

    # -----------------------------------------------------------------------
    # 索引管理
    # -----------------------------------------------------------------------

    def rebuild_index(self, doc_types: Optional[List[str]] = None) -> dict:
        """从头重建索引（遍历所有已索引的文档并重新嵌入）。

        注意：这是一个元操作，仅重建已有的元数据记录。
        实际文档重新索引需要通过各自的源表。
        """
        with self._lock:
            metadata = self._load_metadata()

            if not metadata:
                return {"status": "no_data", "message": "无已索引的文档"}

            # 清除已删除的元数据
            deleted_keys = [k for k, v in metadata.items() if v.get("deleted", False)]
            for k in deleted_keys:
                del metadata[k]
            if deleted_keys:
                logger.info("[VectorSearch] 清除已删除元数据: %d 条", len(deleted_keys))

            # 按类型分组并重新嵌入
            by_type: Dict[str, List[str]] = {}
            for key, info in metadata.items():
                dt = info["doc_type"]
                if doc_types and dt not in doc_types:
                    continue
                by_type.setdefault(dt, []).append(key)

            stats = {}
            for dt, keys in by_type.items():
                texts = [metadata[k]["text"] for k in keys]
                try:
                    vectors = self._embedding.embed(texts)
                    vec_array = np.array(vectors, dtype=np.float32)
                    norms = np.linalg.norm(vec_array, axis=1, keepdims=True)
                    norms = np.where(norms == 0, 1.0, norms)
                    vec_array = vec_array / norms
                    self._save_vectors(dt, vec_array)
                    stats[dt] = {"chunks": len(keys), "status": "rebuilt"}
                    logger.info("[VectorSearch] 重建索引: type=%s chunks=%d", dt, len(keys))
                except Exception as e:
                    stats[dt] = {"chunks": len(keys), "status": "error", "error": str(e)}

            return {"status": "completed", "doc_types": stats}

    def index_status(self) -> dict:
        """获取索引状态统计。"""
        metadata = self._load_metadata()

        by_type: Dict[str, int] = {}
        by_source: Dict[str, int] = {}
        deleted_count = 0
        for key, info in metadata.items():
            if info.get("deleted", False):
                deleted_count += 1
                continue
            dt = info.get("doc_type", "unknown")
            st = info.get("source_table", "unknown")
            by_type[dt] = by_type.get(dt, 0) + 1
            by_source[st] = by_source.get(st, 0) + 1

        return {
            "total_chunks": len(metadata),
            "deleted_chunks": deleted_count,
            "active_chunks": len(metadata) - deleted_count,
            "by_doc_type": by_type,
            "by_source_table": by_source,
            "dimension": self._dim,
            "provider": os.getenv("EMBEDDING_PROVIDER", "local"),
            "base_url": self._embedding.base_url,
            "model": self._embedding.model,
            "data_dir": str(VECTOR_DATA_DIR),
        }
