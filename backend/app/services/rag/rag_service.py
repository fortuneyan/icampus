"""
RAG Service - RAG检索增强服务

统一的RAG服务接口:

用法:
    from app.services.rag import RAGService

    rag = RAGService()

    # 创建知识库
    kb_id = await rag.create_knowledge_base(
        name="课程资料",
        description="数学课程知识点"
    )

    # 添加文档
    await rag.add_document(
        knowledge_base_id=kb_id,
        file_path="/path/to/document.pdf"
    )

    # 检索
    results = await rag.retrieve(
        knowledge_base_id=kb_id,
        query="什么是二次函数",
        top_k=5
    )

    # 对话增强
    response = await rag.augment_chat(
        knowledge_base_id=kb_id,
        query="什么是二次函数",
        history=[]
    )
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from uuid import uuid4

from app.services.rag.embedding import EmbeddingService, get_embedding_service
from app.services.rag.vector_store import VectorStore, get_vector_store_manager
from app.services.rag.document_parser import DocumentParser, get_document_parser


@dataclass
class KnowledgeBase:
    """知识库"""

    id: str
    name: str
    description: str
    document_count: int = 0
    created_at: Optional[str] = None


@dataclass
class RetrievalResult:
    """检索结果"""

    content: str
    source: str
    score: float
    metadata: Dict[str, Any]


class RAGService:
    """RAG服务"""

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.vector_store_manager = get_vector_store_manager()
        self.document_parser = get_document_parser()

    async def create_knowledge_base(
        self,
        name: str,
        description: str = "",
    ) -> str:
        """
        创建知识库

        Returns:
            知识库ID
        """
        kb_id = str(uuid4())[:12]

        # 初始化向量存储
        store = await self.vector_store_manager.get_store(kb_id)

        # 这里可以保存元数据到数据库
        # 实际项目中应保存到PostgreSQL

        return kb_id

    async def delete_knowledge_base(self, knowledge_base_id: str) -> None:
        """删除知识库"""
        await self.vector_store_manager.delete_store(knowledge_base_id)

    async def add_document(
        self,
        knowledge_base_id: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        添加文档到知识库

        Args:
            knowledge_base_id: 知识库ID
            file_path: 文件路径
            metadata: 附加元数据

        Returns:
            添加的段落数
        """
        # 解析文档
        sections = await self.document_parser.parse_file(file_path)

        if not sections:
            return 0

        # 提取文本
        texts = [s.to_text() for s in sections]

        # 生成向量嵌入
        embeddings = await self.embedding_service.embed_texts(texts)

        # 获取向量存储
        store = await self.vector_store_manager.get_store(knowledge_base_id)

        # 构建元数据
        doc_metadata = metadata or {}
        doc_metadata["source_file"] = os.path.basename(file_path)

        metadatas = []
        for section in sections:
            meta = {**doc_metadata}
            meta["title"] = section.title
            meta["level"] = section.level
            if section.page:
                meta["page"] = section.page
            metadatas.append(meta)

        # 添加到向量存储
        ids = [str(uuid4())[:12] for _ in texts]
        await store.add_documents(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        return len(texts)

    async def add_texts(
        self,
        knowledge_base_id: str,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        """
        添加文本到知识库

        Args:
            knowledge_base_id: 知识库ID
            texts: 文本列表
            metadatas: 元数据列表

        Returns:
            添加的数量
        """
        if not texts:
            return 0

        # 生成向量嵌入
        embeddings = await self.embedding_service.embed_texts(texts)

        # 获取向量存储
        store = await self.vector_store_manager.get_store(knowledge_base_id)

        # 构建元数据
        if metadatas is None:
            metadatas = [{} for _ in texts]

        # 添加到向量存储
        ids = [str(uuid4())[:12] for _ in texts]
        await store.add_documents(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        return len(texts)

    async def retrieve(
        self,
        knowledge_base_id: str,
        query: str,
        top_k: int = 5,
    ) -> List[RetrievalResult]:
        """
        语义检索

        Args:
            knowledge_base_id: 知识库ID
            query: 查询文本
            top_k: 返回数量

        Returns:
            检索结果列表
        """
        # 生成查询向量
        query_embedding = await self.embedding_service.embed_query(query)

        # 检索
        store = await self.vector_store_manager.get_store(knowledge_base_id)
        results = await store.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        # 转换结果
        output = []
        for r in results:
            output.append(
                RetrievalResult(
                    content=r["document"],
                    source=r["metadata"].get("source_file", "unknown"),
                    score=1.0 - r["distance"],  # 转换为相似度
                    metadata=r["metadata"],
                )
            )

        return output

    async def augment_chat(
        self,
        knowledge_base_id: str,
        query: str,
        history: List[Dict[str, str]],
        top_k: int = 3,
    ) -> Dict[str, Any]:
        """
        对话增强 - RAG + LLM

        Args:
            knowledge_base_id: 知识库ID
            query: 用户问题
            history: 对话历史 [{"role": "user/assistant", "content": "..."}]
            top_k: 检索数量

        Returns:
            {
                "answer": "LLM生成的答案",
                "sources": [...],  # 检索到的来源
                "context": [...]  # 检索到的上下文
            }
        """
        # 检索相关文档
        results = await self.retrieve(knowledge_base_id, query, top_k)

        if not results:
            return {
                "answer": None,
                "sources": [],
                "context": [],
                "message": "知识库为空，请先添加文���",
            }

        # 构建上下文
        context = "\n\n".join([f"[{i + 1}] {r.content}" for i, r in enumerate(results)])

        # 构建提示
        prompt = f"""基于以下参考资料，回答用户问题。如果没有相关信息，请说明"我不知道"。

参考资料:
{context}

用户问题: {query}

要求:
1. 首先判断参考资料是否包含问题的答案
2. 如果包含，基于参考资料生成答案，并标注来源
3. 如果不包含，直接说明"我不知道"
4. 答案要准确、简洁

请回答:"""

        # 这里调用LLM
        # 实际项目中应调用现有的AIService
        # 为简化暂时返回上下文

        return {
            "answer": None,  # LLM生成的答案
            "sources": [r.source for r in results],
            "context": [r.content for r in results],
            "prompt": prompt,
        }

    async def get_knowledge_base_stats(self, knowledge_base_id: str) -> Dict[str, Any]:
        """获取知识库统计"""
        store = await self.vector_store_manager.get_store(knowledge_base_id)
        count = await store.get_document_count()

        return {
            "document_count": count,
            "knowledge_base_id": knowledge_base_id,
        }


# 全局单例
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """获取全局RAG服务"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
