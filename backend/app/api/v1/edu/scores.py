"""
成绩管理接口
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.schemas.score import ScoreCreate, ScoreUpdate
from app.schemas.response import success, page_response
from app.services.score_service import ScoreService

router = APIRouter()


@router.get("", response_model=dict)
async def get_scores(
    student_id: Optional[UUID] = Query(None),
    course_id: Optional[UUID] = Query(None),
    semester: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取成绩列表"""
    score_service = ScoreService(db)
    result = await score_service.search_scores(
        student_id, course_id, semester, page, page_size
    )

    items = [
        {
            "id": str(s.id),
            "student_id": str(s.student_id),
            "course_id": str(s.course_id),
            "semester": s.semester,
            "score_type": s.score_type,
            "score": float(s.score) if s.score else None,
            "grade_letter": s.grade_letter,
            "rank": s.rank,
            "remarks": s.remarks,
        }
        for s in result["items"]
    ]

    return page_response(items, result["total"], page, page_size)


@router.get("/statistics", response_model=dict)
async def get_score_statistics(
    course_id: UUID,
    semester: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取成绩统计"""
    score_service = ScoreService(db)
    stats = await score_service.get_score_statistics(course_id, semester)
    return success(stats)


@router.get("/{score_id}", response_model=dict)
async def get_score(
    score_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取成绩详情"""
    score_service = ScoreService(db)
    score = await score_service.get(score_id)

    if not score:
        raise NotFoundException("成绩不存在")

    return success(
        {
            "id": str(score.id),
            "student_id": str(score.student_id),
            "course_id": str(score.course_id),
            "semester": score.semester,
            "score_type": score.score_type,
            "score": float(score.score) if score.score else None,
            "grade_letter": score.grade_letter,
            "rank": score.rank,
            "remarks": score.remarks,
        }
    )


@router.post("", response_model=dict)
async def create_score(
    data: ScoreCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建成绩"""
    score_service = ScoreService(db)
    score_data = data.model_dump()
    score_data["recorded_by"] = current_user.id
    score = await score_service.create_score(score_data)
    return success({"id": str(score.id)}, "成绩创建成功")


@router.put("/{score_id}", response_model=dict)
async def update_score(
    score_id: UUID,
    data: ScoreUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新成绩"""
    score_service = ScoreService(db)
    score = await score_service.update_score(
        score_id, data.model_dump(exclude_unset=True)
    )
    return success({"id": str(score.id)}, "成绩更新成功")


@router.delete("/{score_id}", response_model=dict)
async def delete_score(
    score_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除成绩"""
    score_service = ScoreService(db)
    await score_service.delete(score_id)
    return success(message="成绩删除成功")
