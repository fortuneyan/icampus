"""
成绩管理接口
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.score import Score
from app.schemas.response import success, page_response

router = APIRouter()


def parse_uuid(value: Optional[str]) -> Optional[UUID]:
    """解析UUID参数"""
    if not value:
        return None
    try:
        return UUID(value)
    except (ValueError, AttributeError):
        return None


@router.get("", response_model=dict)
async def get_scores(
    student_name: Optional[str] = Query(None, description="学生姓名"),
    student_id: Optional[str] = Query(None, description="学生ID"),
    course_id: Optional[str] = Query(None, description="课程ID"),
    exam_type: Optional[str] = Query(None, description="考试类型"),
    semester: Optional[str] = Query(None, description="学期"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取成绩列表"""
    query = select(Score).order_by(Score.recorded_at.desc())

    if student_id:
        uid = parse_uuid(student_id)
        if uid:
            query = query.where(Score.student_id == uid)

    if course_id:
        uid = parse_uuid(course_id)
        if uid:
            query = query.where(Score.course_id == uid)

    if exam_type:
        query = query.where(Score.score_type == exam_type)

    if semester:
        query = query.where(Score.semester == semester)

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    scores = result.scalars().all()

    items = [
        {
            "id": str(s.id),
            "student_id": str(s.student_id),
            "course_id": str(s.course_id),
            "exam_type": s.score_type,
            "semester": s.semester,
            "score": float(s.score) if s.score else None,
            "grade_letter": s.grade_letter,
            "rank": s.rank,
            "remarks": s.remarks,
        }
        for s in scores
    ]

    return page_response(items, total, page, page_size)


@router.get("/statistics", response_model=dict)
async def get_score_statistics(
    course_id: Optional[str] = Query(None, description="课程ID"),
    semester: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取成绩统计"""
    query = select(Score)

    if course_id:
        uid = parse_uuid(course_id)
        if uid:
            query = query.where(Score.course_id == uid)

    if semester:
        query = query.where(Score.semester == semester)

    result = await db.execute(query)
    scores = result.scalars().all()

    score_list = [s.score for s in scores if s.score]
    if score_list:
        avg_score = sum(score_list) / len(score_list)
        max_score = max(score_list)
        min_score = min(score_list)
    else:
        avg_score = max_score = min_score = 0

    return success(
        {
            "total": len(scores),
            "average": round(avg_score, 2),
            "max": max_score,
            "min": min_score,
        }
    )


@router.get("/{score_id}", response_model=dict)
async def get_score(
    score_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取成绩详情"""
    result = await db.execute(select(Score).where(Score.id == score_id))
    score = result.scalar_one_or_none()

    if not score:
        return success(None)

    return success(
        {
            "id": str(score.id),
            "student_id": str(score.student_id),
            "course_id": str(score.course_id),
            "exam_type": score.score_type,
            "semester": score.semester,
            "score": float(score.score) if score.score else None,
            "grade_letter": score.grade_letter,
            "rank": score.rank,
            "remarks": score.remarks,
        }
    )


@router.post("", response_model=dict)
async def create_score(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建成绩"""
    score = Score(**data)
    db.add(score)
    await db.commit()
    await db.refresh(score)
    return success({"id": str(score.id)}, "成绩创建成功")


@router.put("/{score_id}", response_model=dict)
async def update_score(
    score_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新成绩"""
    result = await db.execute(select(Score).where(Score.id == score_id))
    score = result.scalar_one_or_none()

    if not score:
        return success(message="成绩不存在")

    for key, value in data.items():
        setattr(score, key, value)

    await db.commit()
    return success({"id": str(score.id)}, "成绩更新成功")


@router.delete("/{score_id}", response_model=dict)
async def delete_score(
    score_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除成绩"""
    result = await db.execute(select(Score).where(Score.id == score_id))
    score = result.scalar_one_or_none()

    if score:
        await db.delete(score)
        await db.commit()

    return success(message="成绩删除成功")
