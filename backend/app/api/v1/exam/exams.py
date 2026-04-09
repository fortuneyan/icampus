"""
考试管理接口
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.exam import PaperCreate, PaperUpdate, QuestionCreate
from app.schemas.response import success, page_response
from app.services.exam_service import PaperService, QuestionService

router = APIRouter()


@router.get("/papers", response_model=dict)
async def get_papers(
    page: int = Query(1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PaperService(db)
    result = await service.paginate(page, page_size, [], "created_at", True)
    items = [
        {
            "id": str(p.id),
            "title": p.title,
            "paper_type": p.paper_type,
            "total_score": float(p.total_score),
            "duration": p.duration,
            "status": p.status,
        }
        for p in result["items"]
    ]
    return page_response(items, result["total"], page, page_size)


@router.post("/papers", response_model=dict)
async def create_paper(
    data: PaperCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PaperService(db)
    paper = await service.create_paper(data.model_dump(), current_user.id)
    return success({"id": str(paper.id)}, "创建成功")


@router.get("/questions", response_model=dict)
async def get_questions(
    keyword: Optional[str] = Query(None),
    question_type: Optional[str] = Query(None),
    difficulty: Optional[int] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = QuestionService(db)
    result = await service.search_questions(
        keyword, question_type, difficulty, page, page_size
    )
    items = [
        {
            "id": str(q.id),
            "content": q.content[:50],
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "score": float(q.score),
        }
        for q in result["items"]
    ]
    return page_response(items, result["total"], page, page_size)


@router.post("/questions", response_model=dict)
async def create_question(
    data: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = QuestionService(db)
    question = await service.create_question(data.model_dump(), current_user.id)
    return success({"id": str(question.id)}, "创建成功")
