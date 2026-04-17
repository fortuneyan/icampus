"""
Knowledge Base API - 知识库管理接口

提供知识库的CRUD和检索接口

路由前缀: /api/v1/ai/knowledge-bases
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, Body
from typing import Optional, List
from pydantic import BaseModel
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.response import success, page_response
from app.services.rag.rag_service import RAGService, get_rag_service

router = APIRouter(prefix="/knowledge-bases", tags=["知识库管理"])


@router.post("", response_model=dict)
async def create_knowledge_base(
    name: str = Query(..., min_length=1, max_length=200),
    description: str = Query(""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建知识库"""
    rag = get_rag_service()
    kb_id = await rag.create_knowledge_base(name, description)

    return success(
        {
            "id": kb_id,
            "name": name,
            "description": description,
        },
        "知识库创建成功",
    )


@router.get("", response_model=dict)
async def list_knowledge_bases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取知识库列表"""
    # 实际项目中应从数据库查询
    # 这里返回示例数据
    items = [
        {
            "id": "kb001",
            "name": "数学教材",
            "description": "高中数学知识点",
            "document_count": 100,
            "created_at": "2024-01-01T00:00:00",
        }
    ]

    total = len(items)
    return page_response(items, total, page, page_size)


@router.get("/{knowledge_base_id}", response_model=dict)
async def get_knowledge_base(
    knowledge_base_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取知识库详情"""
    rag = get_rag_service()
    stats = await rag.get_knowledge_base_stats(knowledge_base_id)

    return success(
        {
            "id": knowledge_base_id,
            "stats": stats,
        }
    )


@router.delete("/{knowledge_base_id}", response_model=dict)
async def delete_knowledge_base(
    knowledge_base_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除知识库"""
    rag = get_rag_service()
    await rag.delete_knowledge_base(knowledge_base_id)

    return success(None, "知识库删除成功")


@router.post("/{knowledge_base_id}/documents", response_model=dict)
async def add_document(
    knowledge_base_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传文档到知识库"""
    import tempfile
    import os

    # 保存上传文件
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
    if file_ext not in [".pdf", ".docx", ".doc", ".txt", ".md"]:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    # 创建临时文件
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"{uuid4().hex}{file_ext}")

    try:
        # 写入文件
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        # 添加到知识库
        rag = get_rag_service()
        count = await rag.add_document(knowledge_base_id, temp_path)

        return success(
            {
                "document_count": count,
                "filename": file.filename,
            },
            f"文档添加成功，共{count}个段落",
        )

    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/{knowledge_base_id}/documents", response_model=dict)
async def list_documents(
    knowledge_base_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取知识库文档列表"""
    # 实际项目中应从数据库查询
    return page_response([], 0, page, page_size)


@router.post("/{knowledge_base_id}/texts", response_model=dict)
async def add_texts(
    knowledge_base_id: str,
    texts: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量添加文本到知识库"""
    if not texts:
        raise HTTPException(status_code=400, detail="文本列表为空")

    rag = get_rag_service()
    count = await rag.add_texts(knowledge_base_id, texts)

    return success(
        {
            "count": count,
        },
        f"成功添加{count}条文本",
    )


class RetrieveRequest(BaseModel):
    knowledge_base_id: str
    query: str
    top_k: int = 5


class AugmentRequest(BaseModel):
    knowledge_base_id: str
    query: str
    history: Optional[List[dict]] = []
    top_k: int = 3


@router.post("/retrieve", response_model=dict)
async def retrieve(
    request: RetrieveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """语义检索"""
    rag = get_rag_service()
    results = await rag.retrieve(
        request.knowledge_base_id, request.query, request.top_k
    )

    return success(
        {
            "query": request.query,
            "results": [
                {
                    "content": r.content,
                    "source": r.source,
                    "score": round(r.score, 4),
                    "metadata": r.metadata,
                }
                for r in results
            ],
        }
    )


@router.post("/augment", response_model=dict)
async def augment_chat(
    request: AugmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """对话增强"""
    rag = get_rag_service()
    result = await rag.augment_chat(
        request.knowledge_base_id, request.query, request.history, request.top_k
    )

    return success(result)


def include_router(app):
    """注册路由到FastAPI"""
    from app.api.v1 import api_router

    api_router.include_router(router)
