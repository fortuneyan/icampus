"""
RAG Retrieval API - 语义检索接口

路由前缀: /api/v1/ai/retrieval
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.response import success
from app.services.rag.rag_service import get_rag_service

router = APIRouter(prefix="/retrieval", tags=["语义检索"])


class RetrieveRequest(BaseModel):
    knowledge_base_id: str
    query: str
    top_k: int = 5


class AugmentRequest(BaseModel):
    knowledge_base_id: str
    query: str
    history: Optional[List[dict]] = []
    top_k: int = 3


@router.post("", response_model=dict)
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
    """对话增强 - 返回RAG上下文"""
    rag = get_rag_service()
    result = await rag.augment_chat(
        request.knowledge_base_id, request.query, request.history or [], request.top_k
    )

    return success(result)
