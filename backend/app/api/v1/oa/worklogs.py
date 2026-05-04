"""
工作日志API
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.oa.worklog import WorklogCreate as WorkLogCreate, WorklogUpdate as WorkLogUpdate, WorklogUpdate as WorkLogReview
from app.schemas.response import success, page_response
from app.services.oa.worklog_svc import WorkLogService

router = APIRouter()


# ============ 特定路由必须在 /{log_id} 之前 ============

@router.get("/my", response_model=dict)
async def get_my_worklogs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    log_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的日志"""
    service = WorkLogService(db)
    result = await service.get_my_logs(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        log_type=log_type,
        start_date=start_date,
        end_date=end_date,
    )
    return page_response(result["items"], result["total"], page, page_size)


@router.get("/team/worklogs", response_model=dict)
async def get_team_worklogs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取团队日志(主任查看)"""
    service = WorkLogService(db)
    result = await service.get_team_logs(
        reviewer_id=current_user.id,
        page=page,
        page_size=page_size,
        start_date=start_date,
        end_date=end_date,
    )
    return page_response(result["items"], result["total"], page, page_size)


@router.get("/stats", response_model=dict)
async def get_worklog_stats(
    year: int = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取统计报表"""
    service = WorkLogService(db)
    stats = await service.get_stats(current_user.id, year)
    return success(stats)


# ============ 其他特定路由必须在 /{log_id} 之前 ============

@router.get("/subordinates", response_model=dict)
async def get_subordinate_worklogs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取下属日志"""
    service = WorkLogService(db)
    result = await service.get_team_logs(
        reviewer_id=current_user.id,
        page=page,
        page_size=page_size,
        start_date=start_date,
        end_date=end_date,
    )
    return page_response(result["items"], result["total"], page, page_size)


@router.get("/statistics", response_model=dict)
async def get_worklog_statistics(
    year: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取统计报表"""
    service = WorkLogService(db)
    stats = await service.get_stats(current_user.id, year)
    return success(stats)


@router.get("/weekly-report", response_model=dict)
async def get_weekly_report(
    year: Optional[int] = Query(None),
    week: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取周报"""
    service = WorkLogService(db)
    report = await service.get_weekly_report(current_user.id, year, week)
    return success(report)


@router.get("/monthly-report", response_model=dict)
async def get_monthly_report(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取月报"""
    service = WorkLogService(db)
    report = await service.get_monthly_report(current_user.id, year, month)
    return success(report)


@router.get("/{log_id}/comments", response_model=dict)
async def get_worklog_comments(
    log_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取日志评论"""
    service = WorkLogService(db)
    result = await service.get_comments(log_id, page, page_size)
    return page_response(result["items"], result["total"], page, page_size)


# ============ 列表和创建 ============

@router.get("", response_model=dict)
async def get_worklogs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    log_type: Optional[str] = Query(None),
    author_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取工作日志列表"""
    service = WorkLogService(db)
    result = await service.get_list(
        page=page,
        page_size=page_size,
        log_type=log_type,
        author_id=UUID(author_id) if author_id else None,
        start_date=start_date,
        end_date=end_date,
        current_user=current_user,
    )
    return page_response(result["items"], result["total"], page, page_size)


@router.post("", response_model=dict)
async def create_worklog(
    data: WorkLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建工作日志"""
    service = WorkLogService(db)
    log = await service.create_log(data.model_dump(), current_user.id)
    return success({"id": str(log.id)}, "工作日志创建成功")


# ============ 单条操作 - 动态路由必须在特定路由之后 ============

@router.get("/{log_id}", response_model=dict)
async def get_worklog_detail(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取工作日志详情"""
    service = WorkLogService(db)
    detail = await service.get_log_detail(log_id)
    return success(detail)


@router.put("/{log_id}", response_model=dict)
async def update_worklog(
    log_id: UUID,
    data: WorkLogUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """编辑工作日志"""
    service = WorkLogService(db)
    log = await service.update_log(log_id, data.model_dump(exclude_unset=True), current_user.id)
    return success({"id": str(log.id)}, "工作日志更新成功")


@router.delete("/{log_id}", response_model=dict)
async def delete_worklog(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除工作日志"""
    service = WorkLogService(db)
    await service.delete_log(log_id, current_user.id)
    return success(message="工作日志删除成功")


@router.post("/{log_id}/submit", response_model=dict)
async def submit_worklog(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交审核"""
    service = WorkLogService(db)
    log = await service.submit_log(log_id, current_user.id)
    return success({"id": str(log.id)}, "工作日志已提交")


@router.post("/{log_id}/comment", response_model=dict)
async def comment_worklog(
    log_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """评论日志"""
    service = WorkLogService(db)
    comment = await service.add_comment(log_id, current_user.id, data.get("content", ""))
    return success({"id": str(comment.id)}, "评论成功")


@router.post("/{log_id}/like", response_model=dict)
async def like_worklog(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """点赞日志"""
    service = WorkLogService(db)
    await service.like_log(log_id, current_user.id)
    return success(message="点赞成功")


@router.post("/{log_id}/unlike", response_model=dict)
async def unlike_worklog(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取消点赞"""
    service = WorkLogService(db)
    await service.unlike_log(log_id, current_user.id)
    return success(message="已取消点赞")


@router.delete("/{log_id}/comments/{comment_id}", response_model=dict)
async def delete_comment(
    log_id: UUID,
    comment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除评论"""
    service = WorkLogService(db)
    await service.delete_comment(comment_id, current_user.id)
    return success(message="评论已删除")


@router.post("/{log_id}/review", response_model=dict)
async def review_worklog(
    log_id: UUID,
    data: WorkLogReview,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """审核日志"""
    service = WorkLogService(db)
    log = await service.review_log(log_id, current_user.id, data.model_dump())
    return success({"id": str(log.id)}, "审核完成")
