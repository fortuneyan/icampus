"""
报表接口
"""

from typing import Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.report import ReportQuery, CustomReportCreate
from app.schemas.response import success, page_response
from app.services.report_service import ReportService

router = APIRouter()


@router.get("/student", response_model=dict)
async def get_student_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReportService(db)
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    data = await service.get_student_report(start, end)
    return success(data)


@router.get("/score", response_model=dict)
async def get_score_report(
    course_id: Optional[UUID] = Query(None),
    semester: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReportService(db)
    data = await service.get_score_report(course_id, semester)
    return success(data)


@router.get("/attendance", response_model=dict)
async def get_attendance_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReportService(db)
    start = datetime.fromisoformat(start_date) if start_date else datetime.now()
    end = datetime.fromisoformat(end_date) if end_date else datetime.now()
    data = await service.get_attendance_report(start, end, current_user.id)
    return success(data)


@router.post("/custom", response_model=dict)
async def create_custom_report(
    data: CustomReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReportService(db)
    result = await service.create_custom_report(
        current_user.id, data.name, data.report_type, data.config, data.is_public
    )
    return success(result, "创建成功")
