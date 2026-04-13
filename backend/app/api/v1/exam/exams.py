"""
考试管理接口

考试(Exam)本身的 CRUD 管理。
试卷管理 → papers.py
题库管理 → question_bank.py
成绩报表 → reports.py
质量评分 → quality_score.py
"""

from typing import Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.exam import ExamPaper
from app.schemas.response import success, page_response

router = APIRouter()


# ==================== Schema ====================

class ExamCreate(BaseModel):
    """创建考试"""
    title: str = Field(..., max_length=200, description="考试名称")
    exam_type: str = Field(default="exam", description="考试类型: midterm/final/quiz/mock/diagnostic")
    academic_year: Optional[str] = Field(None, max_length=20, description="学年")
    semester: Optional[str] = Field(None, max_length=20, description="学期")
    total_score: float = Field(default=100.0, description="总分")
    duration: int = Field(default=90, description="考试时长(分钟)")
    course_id: Optional[UUID] = Field(None, description="课程ID")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")


class ExamUpdate(BaseModel):
    """更新考试"""
    title: Optional[str] = Field(None, max_length=200)
    paper_type: Optional[str] = None
    total_score: Optional[float] = None
    duration: Optional[int] = None
    status: Optional[str] = Field(None, description="状态: draft/published/closed/archived")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


# ==================== 考试 CRUD ====================

@router.get("/exams", response_model=dict, summary="考试列表")
async def list_exams(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    paper_type: Optional[str] = Query(None, description="考试类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, max_length=100, description="关键词搜索"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取考试列表"""
    query = select(ExamPaper).where(ExamPaper.is_deleted == False if hasattr(ExamPaper, 'is_deleted') else True)

    if paper_type:
        query = query.where(ExamPaper.paper_type == paper_type)
    if status:
        query = query.where(ExamPaper.status == status)
    if keyword:
        query = query.where(ExamPaper.title.ilike(f"%{keyword}%"))

    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    query = query.order_by(ExamPaper.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    exams = result.scalars().all()

    items = [
        {
            "id": str(e.id),
            "title": e.title,
            "paper_type": e.paper_type,
            "total_score": float(e.total_score) if e.total_score else 0,
            "duration": e.duration,
            "status": e.status,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in exams
    ]
    return page_response(items, total, page, page_size)


@router.post("/exams", response_model=dict, summary="创建考试")
async def create_exam(
    data: ExamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建考试"""
    exam = ExamPaper(
        title=data.title,
        paper_type=data.exam_type,
        total_score=data.total_score,
        duration=data.duration,
        course_id=data.course_id,
        creator_id=current_user.id,
        status="draft",
    )
    db.add(exam)
    await db.commit()
    await db.refresh(exam)
    return success({"id": str(exam.id), "title": exam.title}, "创建成功")


@router.get("/exams/{exam_id}", response_model=dict, summary="考试详情")
async def get_exam(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取考试详情"""
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    return success({
        "id": str(exam.id),
        "title": exam.title,
        "paper_type": exam.paper_type,
        "total_score": float(exam.total_score) if exam.total_score else 0,
        "duration": exam.duration,
        "status": exam.status,
        "course_id": str(exam.course_id) if exam.course_id else None,
        "creator_id": str(exam.creator_id) if exam.creator_id else None,
        "created_at": exam.created_at.isoformat() if exam.created_at else None,
        "updated_at": exam.updated_at.isoformat() if exam.updated_at else None,
    })


@router.put("/exams/{exam_id}", response_model=dict, summary="更新考试")
async def update_exam(
    exam_id: UUID,
    data: ExamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新考试信息"""
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(exam, field, value)

    await db.commit()
    return success({"id": str(exam.id)}, "更新成功")


@router.delete("/exams/{exam_id}", response_model=dict, summary="删除考试")
async def delete_exam(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除考试"""
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    if hasattr(exam, 'is_deleted'):
        exam.is_deleted = True
    else:
        await db.delete(exam)
    await db.commit()
    return success(None, "删除成功")


@router.post("/exams/{exam_id}/publish", response_model=dict, summary="发布考试")
async def publish_exam(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发布考试"""
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    exam.status = "published"
    await db.commit()
    return success({"id": str(exam.id), "status": exam.status}, "发布成功")
