# -*- coding: utf-8 -*-
"""
===================================
嵌入服务 — 全量通过 LM Studio / OpenAI 兼容 API
===================================

本地模式：
  → 调用 LM Studio http://localhost:1234/v1/embeddings
  → 不需要任何 Python 模型库
  → LM Studio 负责 GPU 推理

Remote 模式：
  → 调用云端 API /v1/embeddings
  → 由 EMBEDDING_BASE_URL 指定

两种模式本质相同，只是 base_url 不同。
"""

import logging
import os
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)


class EmbeddingService:
    """嵌入服务 — 通过 LM Studio / OpenAI 兼容 API 获取向量。

    配置：
      EMBEDDING_PROVIDER=local (默认) | remote
      EMBEDDING_BASE_URL=http://localhost:1234/v1 (默认)
      EMBEDDING_API_KEY=not-needed (默认)
      EMBEDDING_MODEL=text-embedding-baai-bge-m3-568m (默认)
      EMBEDDING_DIMENSION=1024 (默认, bge-m3 输出 1024 维)
      EMBEDDING_TIMEOUT=30 (默认)
    """

    _instance: Optional["EmbeddingService"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
        if provider == "remote":
            raw_url = os.getenv("EMBEDDING_BASE_URL", "")
            if not raw_url:
                raise ValueError(
                    "EMBEDDING_PROVIDER=remote 但未设置 EMBEDDING_BASE_URL。"
                    "请设置 EMBEDDING_BASE_URL 指向你的 API 端点"
                    "（如 http://your-server:1234/v1）。"
                )
            default_url = raw_url
        else:
            default_url = "http://localhost:1234/v1"

        self.base_url: str = os.getenv("EMBEDDING_BASE_URL", default_url).rstrip("/")
        self.api_key: str = os.getenv("EMBEDDING_API_KEY", "not-needed")
        self.model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-baai-bge-m3-568m")
        self._dim: int = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
        self._timeout: int = int(os.getenv("EMBEDDING_TIMEOUT", "30"))

        logger.info(
            "[Embedding] 初始化: provider=%s base_url=%s model=%s dim=%d",
            provider, self.base_url, self.model, self._dim,
        )
        self._initialized = True

    def embed(self, texts: List[str]) -> List[List[float]]:
        """批量文本向量化。

        调用 {base_url}/embeddings (OpenAI 兼容格式)

        Args:
            texts: 文本列表

        Returns:
            向量列表，shape (len(texts), dimension)
        """
        if not texts:
            return []

        try:
            resp = requests.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"input": texts, "model": self.model},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            data = resp.json()

            # 按 index 排序以保持输入顺序
            items = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in items]

        except requests.ConnectionError:
            logger.error(
                "[Embedding] 无法连接到 %s。请确保 LM Studio 已启动并加载了 embedding 模型。",
                self.base_url,
            )
            raise
        except Exception as e:
            logger.error("[Embedding] API 调用失败: %s", e)
            raise

    def embed_query(self, query: str) -> List[float]:
        """单条查询向量化。"""
        return self.embed([query])[0]

    @property
    def dimension(self) -> int:
        return self._dim
