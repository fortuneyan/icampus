"""
Embedding Service - 向量嵌入服务

支持多种Embedding Provider:
1. sentence-transformers (本地模型)
2. OpenAI Embedding
3. Ollama Embedding

用法:
    from app.services.rag.embedding import EmbeddingService, EmbeddingProvider

    # 使用本地模型
    service = EmbeddingService(EmbeddingProvider.SENTENCE_TRANSFORMERS)

    # 使用OpenAI
    service = EmbeddingService(EmbeddingProvider.OPENAI, api_key="sk-...")

    embeddings = await service.embed_texts(["文本1", "文本2"])
"""

import os
from enum import Enum
from typing import List, Optional, Union
import numpy as np

import httpx
from app.core.config import settings


class EmbeddingProvider(str, Enum):
    """Embedding提供者"""

    SENTENCE_TRANSFORMERS = "sentence_transformers"  # 本地模型
    OPENAI = "openai"  # OpenAI
    OLLAMA = "ollama"  # Ollama本地
    JINA = "jina"  # Jina AI


class EmbeddingService:
    """Embedding服务"""

    DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"  # 中文BGE模型

    def __init__(
        self,
        provider: EmbeddingProvider = EmbeddingProvider.SENTENCE_TRANSFORMERS,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.provider = provider
        self.model_name = model_name or self.DEFAULT_MODEL
        self.api_key = api_key or os.getenv("EMBEDDING_API_KEY", "")
        self.base_url = base_url
        self._model = None

    async def initialize(self) -> None:
        """初始化模型"""
        if self.provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. Run: pip install sentence-transformers"
                )

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        将文本转换为向量嵌入

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        if not texts:
            return []

        # 确保模型已初始化
        if self._model is None:
            await self.initialize()

        if self.provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
            return await self._embed_local(texts)
        elif self.provider == EmbeddingProvider.OPENAI:
            return await self._embed_openai(texts)
        elif self.provider == EmbeddingProvider.OLLAMA:
            return await self._embed_ollama(texts)
        elif self.provider == EmbeddingProvider.JINA:
            return await self._embed_jina(texts)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    async def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """本地模型嵌入"""
        import asyncio

        embeddings = await asyncio.get_event_loop().run_in_executor(
            None, self._model.encode, texts
        )
        return embeddings.tolist()

    async def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """OpenAI嵌入"""
        if not self.api_key:
            raise ValueError("OpenAI API key required")

        base_url = self.base_url or "https://api.openai.com/v1"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/embeddings",
                json={
                    "input": texts,
                    "model": "text-embedding-3-small",
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]

    async def _embed_ollama(self, texts: List[str]) -> List[List[float]]:
        """Ollama嵌入"""
        base_url = self.base_url or "http://localhost:11434"
        async with httpx.AsyncClient() as client:
            results = []
            for text in texts:
                response = await client.post(
                    f"{base_url}/api/embeddings",
                    json={
                        "model": self.model_name,
                        "prompt": text,
                    },
                )
                response.raise_for_status()
                data = response.json()
                results.append(data["embedding"])
            return results

    async def _embed_jina(self, texts: List[str]) -> List[List[float]]:
        """Jina AI嵌入"""
        async with httpx.AsyncClient() as client:
            results = []
            for text in texts:
                # URL编码文本
                import urllib.parse

                encoded = urllib.parse.quote(text)
                response = await client.get(
                    f"https://api.jina.ai/v1/embeddings",
                    params={"text": text},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                response.raise_for_status()
                data = response.json()
                results.append(data["embedding"])
            return results

    async def embed_query(self, query: str) -> List[float]:
        """嵌入单个查询"""
        results = await self.embed_texts([query])
        return results[0] if results else []

    async def get_embedding_dimension(self) -> int:
        """获取向量维度"""
        if self._model is None:
            await self.initialize()

        if self.provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
            return self._model.get_sentence_embedding_dimension()
        elif self.provider == EmbeddingProvider.OPENAI:
            return 1536  # text-embedding-3-small
        elif self.provider == EmbeddingProvider.OLLAMA:
            return 768  # 默认
        else:
            return 768


# 全局单例
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """获取全局Embedding服务实例"""
    global _embedding_service
    if _embedding_service is None:
        provider = EmbeddingProvider(
            os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
        )
        _embedding_service = EmbeddingService(
            provider=provider,
            model_name=os.getenv("EMBEDDING_MODEL", None),
        )
    return _embedding_service
