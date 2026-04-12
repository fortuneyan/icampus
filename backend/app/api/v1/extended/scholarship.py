"""
奖助学金管理接口
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.scholarship import Scholarship, ScholarshipApplication, GrantRecord, PoorStudent
from app.schemas.response import success, page_response

router = APIRouter()


# ==================== 奖学金项目 ====================

class ScholarshipCreate(BaseModel):
    name: str
    scholarship_no: str
    scholarship_type: str  # scholarship/grant/aid
    level: Optional[str] = None
    amount: int  # 分
    quota: Optional[int] = None
    academic_year: str
    semester: str
    requirements: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@router.get("/projects", response_model=dict)
async def get_scholarships(
    keyword: Optional[str] = Query(None),
    scholarship_type: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取奖学金项目列表"""
    query = select(Scholarship).order_by(desc(Scholarship.created_at))
    
    if keyword:
        query = query.where(Scholarship.name.ilike(f"%{keyword}%"))
    if scholarship_type:
        query = query.where(Scholarship.scholarship_type == scholarship_type)
    if academic_year:
        query = query.where(Scholarship.academic_year == academic_year)
    if status:
        query = query.where(Scholarship.status == status)
    
    total_result = await db.execute(query)
    total = len(total_result.scalars().all())
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return page_response([
        {
            "id": str(s.id),
            "name": s.name,
            "scholarship_no": s.scholarship_no,
            "scholarship_type": s.scholarship_type,
            "level": s.level,
            "amount": s.amount / 100.0,  # 转换为元
            "quota": s.quota,
            "academic_year": s.academic_year,
            "semester": s.semester,
            "status": s.status,
        }
        for s in items
    ], total, page, page_size)


@router.post("/projects", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_scholarship(
    data: ScholarshipCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建奖学金项目"""
    scholarship = Scholarship(
        amount=data.amount * 100,  # 转换为分
        start_date=datetime.fromisoformat(data.start_date) if data.start_date else None,
        end_date=datetime.fromisoformat(data.end_date) if data.end_date else None,
        created_by=current_user.id,
        **data.model_dump(exclude={"amount", "start_date", "end_date"})
    )
    db.add(scholarship)
    await db.commit()
    await db.refresh(scholarship)
    return success({"id": str(scholarship.id)}, "创建成功")


# ==================== 奖学金申请 ====================

class ApplicationCreate(BaseModel):
    scholarship_id: UUID
    student_id: UUID
    academic_year: str
    semester: str
    gpa: Optional[str] = None
    rank: Optional[int] = None
    total_students: Optional[int] = None
    application_reason: Optional[str] = None


@router.get("/applications", response_model=dict)
async def get_applications(
    scholarship_id: Optional[UUID] = Query(None),
    student_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取申请列表"""
    query = select(ScholarshipApplication).order_by(desc(ScholarshipApplication.created_at))
    
    if scholarship_id:
        query = query.where(ScholarshipApplication.scholarship_id == scholarship_id)
    if student_id:
        query = query.where(ScholarshipApplication.student_id == student_id)
    if status:
        query = query.where(ScholarshipApplication.status == status)
    
    total_result = await db.execute(query)
    total = len(total_result.scalars().all())
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return page_response([
        {
            "id": str(a.id),
            "scholarship_id": str(a.scholarship_id),
            "student_id": str(a.student_id),
            "academic_year": a.academic_year,
            "semester": a.semester,
            "gpa": a.gpa,
            "rank": a.rank,
            "status": a.status,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in items
    ], total, page, page_size)


@router.post("/applications", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交申请"""
    application = ScholarshipApplication(**data.model_dump())
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return success({"id": str(application.id)}, "申请提交成功")


@router.put("/applications/{application_id}/review", response_model=dict)
async def review_application(
    application_id: UUID,
    status: str = Query(..., description="approved/rejected"),
    comment: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """审核申请"""
    result = await db.execute(
        select(ScholarshipApplication).where(ScholarshipApplication.id == application_id)
    )
    application = result.scalar_one_or_none()
    
    if not application:
        return success(message="申请不存在")
    
    application.status = status
    application.reviewer_id = current_user.id
    application.review_comment = comment
    application.reviewed_at = datetime.utcnow()
    
    await db.commit()
    return success(message="审核完成")


# ==================== 贫困生认定 ====================

class PoorStudentCreate(BaseModel):
    student_id: UUID
    poor_level: str
    academic_year: str
    poor_type: Optional[str] = None
    family_address: Optional[str] = None
    annual_income: Optional[str] = None


@router.get("/poor-students", response_model=dict)
async def get_poor_students(
    academic_year: Optional[str] = Query(None),
    poor_level: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取贫困生列表"""
    query = select(PoorStudent).order_by(desc(PoorStudent.created_at))
    
    if academic_year:
        query = query.where(PoorStudent.academic_year == academic_year)
    if poor_level:
        query = query.where(PoorStudent.poor_level == poor_level)
    if status:
        query = query.where(PoorStudent.status == status)
    
    total_result = await db.execute(query)
    total = len(total_result.scalars().all())
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return page_response([
        {
            "id": str(p.id),
            "student_id": str(p.student_id),
            "poor_level": p.poor_level,
            "poor_type": p.poor_type,
            "academic_year": p.academic_year,
            "status": p.status,
        }
        for p in items
    ], total, page, page_size)


@router.post("/poor-students", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_poor_student(
    data: PoorStudentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建贫困生认定"""
    poor = PoorStudent(
        approved_by=current_user.id,
        approved_at=datetime.utcnow(),
        **data.model_dump()
    )
    db.add(poor)
    await db.commit()
    await db.refresh(poor)
    return success({"id": str(poor.id)}, "认定成功")
