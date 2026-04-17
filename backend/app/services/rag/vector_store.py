"""
Vector Store - 向量存储服务

基于ChromaDB的向量存储实现

用法:
    from app.services.rag.vector_store import VectorStore

    store = VectorStore(persist_directory="./data/vectors")
    await store.initialize("my_knowledge_base")

    # 添加文档
    await store.add_documents(
        ids=["doc1", "doc2"],
        embeddings=[[0.1, 0.2], [0.3, 0.4]],
        documents=["文档内容1", "文档内容2"],
        metadatas=[{"source": "pdf"}, {"source": "docx"}]
    )

    # 检索
    results = await store.search(query_embedding=[0.1, 0.2], top_k=5)
"""

import os
from typing import List, Dict, Any, Optional
import uuid

try:
    import chromadb
    from chromadb.config import SettableClientPayload

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class VectorStore:
    """向量存储服务"""

    def __init__(
        self,
        persist_directory: str = "./data/vectors",
        collection_name: Optional[str] = None,
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name or "default"
        self._client = None
        self._collection = None

    async def initialize(self, collection_name: str) -> None:
        """初始化向量存储"""
        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb not installed. Run: pip install chromadb")

        # 确保目录存在
        os.makedirs(self.persist_directory, exist_ok=True)

        # 创建客户端
        self._client = chromadb.Client(
            Settings(
                persist_directory=self.persist_directory,
                anonymized_telemetry=False,
            )
        )
        self.collection_name = collection_name

        # 获取或创建集合
        try:
            self._collection = self._client.get_collection(collection_name)
        except Exception:
            self._collection = self._client.create_collection(
                collection_name, get_or_create=True
            )

    async def add_documents(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """添加文档到向量存储"""
        if not self._collection:
            raise RuntimeError("VectorStore not initialized. Call initialize() first.")

        # 生成ID
        if not ids:
            ids = [str(uuid.uuid4()) for _ in documents]

        # 确保长度一致
        if len(embeddings) != len(documents):
            raise ValueError(
                f"embeddings ({len(embeddings)}) and documents ({len(documents)}) length mismatch"
            )

        # 添加元数据
        if metadatas is None:
            metadatas = [{} for _ in documents]

        # 批量添加
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """向量相似度检索"""
        if not self._collection:
            raise RuntimeError("VectorStore not initialized. Call initialize() first.")

        # 检索
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
        )

        # 格式化结果
        output = []
        if results["ids"] and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                output.append(
                    {
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i]
                        if results["metadatas"]
                        else {},
                        "distance": results["distances"][0][i]
                        if results["distances"]
                        else 0.0,
                    }
                )

        return output

    async def delete_collection(self) -> None:
        """删除集合"""
        if self._client and self.collection_name:
            try:
                self._client.delete_collection(self.collection_name)
            except Exception:
                pass

    async def getDocumentCount(self) -> int:
        """获取文档数量"""
        if not self._collection:
            return 0
        return self._collection.count()


# 全局向量存储管理器
class VectorStoreManager:
    """向量存储管理器"""

    def __init__(self, persist_directory: str = "./data/vectors"):
        self.persist_directory = persist_directory
        self._stores: Dict[str, VectorStore] = {}

    async def get_store(self, knowledge_base_id: str) -> VectorStore:
        """获取指定知识库的向量存储"""
        if knowledge_base_id not in self._stores:
            store = VectorStore(
                persist_directory=self.persist_directory,
                collection_name=knowledge_base_id,
            )
            await store.initialize(knowledge_base_id)
            self._stores[knowledge_base_id] = store

        return self._stores[knowledge_base_id]

    async def delete_store(self, knowledge_base_id: str) -> None:
        """删除指定知识库的向量存储"""
        if knowledge_base_id in self._stores:
            await self._stores[knowledge_base_id].delete_collection()
            del self._stores[knowledge_base_id]


# 全局管理器
_vector_store_manager: Optional[VectorStoreManager] = None


def get_vector_store_manager() -> VectorStoreManager:
    """获取全局向量存储管理器"""
    global _vector_store_manager
    if _vector_store_manager is None:
        _vector_store_manager = VectorStoreManager()
    return _vector_store_manager
