"""
教学进度跟踪 API 接口

提供教学进度 CRUD、更新记录、进度报告等功能
"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.teaching_progress import (
    TeachingProgress, ProgressUpdate, ProgressReport, ProgressStatus,
)
from app.schemas.response import success, error, page_response

router = APIRouter()


# ==================== 教学进度 CRUD ====================

@router.get("/teaching-progress", summary="获取教学进度列表")
async def list_teaching_progress(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    course_id: Optional[int] = Query(None, description="课程ID筛选"),
    teacher_id: Optional[int] = Query(None, description="教师ID筛选"),
    class_id: Optional[int] = Query(None, description="班级ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取教学进度列表

    - **course_id**: 课程ID筛选
    - **teacher_id**: 教师ID筛选
    - **class_id**: 班级ID筛选
    - **status**: 状态筛选
    - **keyword**: 关键词搜索（章节名、单元名）
    """
    query = select(TeachingProgress).where(TeachingProgress.is_deleted == False)

    if course_id:
        query = query.where(TeachingProgress.course_id == course_id)
    if teacher_id:
        query = query.where(TeachingProgress.teacher_id == teacher_id)
    if class_id:
        query = query.where(TeachingProgress.class_id == class_id)
    if status:
        query = query.where(TeachingProgress.status == status)
    if keyword:
        query = query.where(
            (TeachingProgress.chapter.contains(keyword)) |
            (TeachingProgress.unit_name.contains(keyword))
        )

    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    query = query.order_by(TeachingProgress.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    progresses = result.scalars().all()

    return page_response(
        [p.to_dict() for p in progresses],
        total,
        page,
        page_size,
    )


@router.get("/teaching-progress/{progress_id}", summary="获取教学进度详情")
async def get_teaching_progress(
    progress_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教学进度详情"""
    result = await db.execute(
        select(TeachingProgress).where(
            TeachingProgress.id == progress_id,
            TeachingProgress.is_deleted == False,
        )
    )
    progress = result.scalar_one_or_none()
    if not progress:
        raise HTTPException(status_code=404, detail="教学进度不存在")
    return success(progress.to_dict())


@router.post("/teaching-progress", summary="创建教学进度")
async def create_teaching_progress(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建教学进度

    必填字段：
    - **course_id**: 课程ID
    """
    if not data.get("course_id"):
        raise HTTPException(status_code=400, detail="课程ID不能为空")

    progress = TeachingProgress(**data)
    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    return success(progress.to_dict(), "创建成功")


@router.put("/teaching-progress/{progress_id}", summary="更新教学进度")
async def update_teaching_progress(
    progress_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新教学进度"""
    result = await db.execute(
        select(TeachingProgress).where(
            TeachingProgress.id == progress_id,
            TeachingProgress.is_deleted == False,
        )
    )
    progress = result.scalar_one_or_none()
    if not progress:
        raise HTTPException(status_code=404, detail="教学进度不存在")

    # 记录更新日志
    for key, value in data.items():
        if hasattr(progress, key) and getattr(progress, key) != value:
            update_log = ProgressUpdate(
                progress_id=progress_id,
                update_type=key,
                old_value=str(getattr(progress, key)),
                new_value=str(value),
            )
            db.add(update_log)

        if hasattr(progress, key):
            setattr(progress, key, value)

    await db.commit()
    await db.refresh(progress)
    return success(progress.to_dict(), "更新成功")


@router.delete("/teaching-progress/{progress_id}", summary="删除教学进度")
async def delete_teaching_progress(
    progress_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除教学进度（软删除）"""
    result = await db.execute(
        select(TeachingProgress).where(TeachingProgress.id == progress_id)
    )
    progress = result.scalar_one_or_none()
    if not progress:
        raise HTTPException(status_code=404, detail="教学进度不存在")

    progress.soft_delete()
    await db.commit()
    return success(None, "删除成功")


@router.patch("/teaching-progress/{progress_id}/percentage", summary="更新完成百分比")
async def update_progress_percentage(
    progress_id: int,
    percentage: float = Query(..., ge=0, le=100, description="完成百分比"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新完成百分比

    - **percentage**: 完成百分比 (0-100)
    """
    result = await db.execute(
        select(TeachingProgress).where(
            TeachingProgress.id == progress_id,
            TeachingProgress.is_deleted == False,
        )
    )
    progress = result.scalar_one_or_none()
    if not progress:
        raise HTTPException(status_code=404, detail="教学进度不存在")

    old_percentage = progress.progress_percentage
    progress.progress_percentage = min(100.0, max(0.0, percentage))

    # 自动更新状态
    if percentage >= 100:
        progress.status = ProgressStatus.COMPLETED
        progress.actual_end_date = date.today()
    elif percentage > 0:
        progress.status = ProgressStatus.IN_PROGRESS
        if not progress.actual_start_date:
            progress.actual_start_date = date.today()

    # 记录更新
    update_log = ProgressUpdate(
        progress_id=progress_id,
        update_type="progress_percentage",
        old_value=str(old_percentage),
        new_value=str(percentage),
    )
    db.add(update_log)

    await db.commit()
    await db.refresh(progress)
    return success(progress.to_dict(), "更新成功")


# ==================== 进度更新记录 ====================

@router.get("/progress-updates/{progress_id}", summary="获取进度更新记录")
async def get_progress_updates(
    progress_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取进度更新记录"""
    result = await db.execute(
        select(ProgressUpdate)
        .where(ProgressUpdate.progress_id == progress_id)
        .order_by(ProgressUpdate.created_at.desc())
    )
    updates = result.scalars().all()
    return success([u.to_dict() for u in updates])


# ==================== 进度报告 ====================

@router.get("/progress-reports", summary="获取进度报告列表")
async def list_progress_reports(
    teacher_id: Optional[int] = Query(None),
    report_type: Optional[str] = Query(None),
    school_year: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取进度报告列表"""
    query = select(ProgressReport)

    if teacher_id:
        query = query.where(ProgressReport.teacher_id == teacher_id)
    if report_type:
        query = query.where(ProgressReport.report_type == report_type)
    if school_year:
        query = query.where(ProgressReport.school_year == school_year)
    if semester:
        query = query.where(ProgressReport.semester == semester)

    result = await db.execute(query.order_by(ProgressReport.created_at.desc()))
    reports = result.scalars().all()
    return success([r.to_dict() for r in reports])


@router.get("/progress-reports/{report_id}", summary="获取报告详情")
async def get_progress_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取报告详情"""
    result = await db.execute(
        select(ProgressReport).where(ProgressReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return success(report.to_dict())


@router.post("/progress-reports", summary="创建进度报告")
async def create_progress_report(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建进度报告"""
    if not data.get("title"):
        raise HTTPException(status_code=400, detail="报告标题不能为空")

    report = ProgressReport(**data)
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return success(report.to_dict(), "创建成功")


@router.post("/progress-reports/{report_id}/submit", summary="提交进度报告")
async def submit_progress_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交进度报告"""
    result = await db.execute(
        select(ProgressReport).where(ProgressReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    report.status = "submitted"
    await db.commit()
    await db.refresh(report)
    return success(report.to_dict(), "提交成功")


@router.post("/progress-reports/{report_id}/approve", summary="审批进度报告")
async def approve_progress_report(
    report_id: int,
    reviewed_by: str = Query(..., description="审核人"),
    comments: Optional[str] = Query(None, description="审核意见"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """审批进度报告"""
    result = await db.execute(
        select(ProgressReport).where(ProgressReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    report.status = "approved"
    report.reviewed_by = reviewed_by
    report.reviewed_at = date.today()
    report.review_comments = comments
    await db.commit()
    await db.refresh(report)
    return success(report.to_dict(), "审批成功")


# ==================== 统计分析 ====================

@router.get("/statistics/teacher/{teacher_id}", summary="获取教师教学统计")
async def get_teacher_statistics(
    teacher_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教师教学统计"""
    result = await db.execute(
        select(TeachingProgress).where(
            TeachingProgress.teacher_id == teacher_id,
            TeachingProgress.is_deleted == False,
        )
    )
    progresses = result.scalars().all()

    total = len(progresses)
    completed = len([p for p in progresses if p.status == ProgressStatus.COMPLETED])
    in_progress = len([p for p in progresses if p.status == ProgressStatus.IN_PROGRESS])
    delayed = len([p for p in progresses if p.status == ProgressStatus.DELAYED])

    avg_percentage = sum(p.progress_percentage for p in progresses) / total if total > 0 else 0

    return success({
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "delayed": delayed,
        "avg_progress": round(avg_percentage, 2),
        "completion_rate": round(completed / total * 100, 2) if total > 0 else 0,
    })


@router.get("/statistics/course/{course_id}", summary="获取课程教学统计")
async def get_course_statistics(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取课程教学统计"""
    result = await db.execute(
        select(TeachingProgress).where(
            TeachingProgress.course_id == course_id,
            TeachingProgress.is_deleted == False,
        )
    )
    progresses = result.scalars().all()

    total = len(progresses)
    avg_percentage = sum(p.progress_percentage for p in progresses) / total if total > 0 else 0

    return success({
        "total_chapters": total,
        "avg_progress": round(avg_percentage, 2),
        "status_distribution": {
            "not_started": len([p for p in progresses if p.status == ProgressStatus.NOT_STARTED]),
            "in_progress": len([p for p in progresses if p.status == ProgressStatus.IN_PROGRESS]),
            "completed": len([p for p in progresses if p.status == ProgressStatus.COMPLETED]),
            "delayed": len([p for p in progresses if p.status == ProgressStatus.DELAYED]),
        },
    })
