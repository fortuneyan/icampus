"""
教研课题接口
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.research import ResearchProject
from app.schemas.response import success, page_response

router = APIRouter()


class ResearchProjectCreate(BaseModel):
    leader_id: UUID
    project_no: str
    title: str
    project_type: Optional[str] = None
    background: Optional[str] = None
    objectives: Optional[str] = None
    content: Optional[str] = None
    methods: Optional[str] = None
    expected_results: Optional[str] = None
    funding: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = "pending"
    members: Optional[str] = None
    attachments: Optional[str] = None
    remarks: Optional[str] = None


class ResearchProjectUpdate(BaseModel):
    project_no: Optional[str] = None
    title: Optional[str] = None
    project_type: Optional[str] = None
    background: Optional[str] = None
    objectives: Optional[str] = None
    content: Optional[str] = None
    methods: Optional[str] = None
    expected_results: Optional[str] = None
    funding: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    members: Optional[str] = None
    attachments: Optional[str] = None
    remarks: Optional[str] = None


@router.get("", response_model=dict)
async def get_research_projects(
    leader_id: Optional[UUID] = Query(None),
    project_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教研课题列表"""
    query = select(ResearchProject).order_by(desc(ResearchProject.created_at))

    if leader_id:
        query = query.where(ResearchProject.leader_id == leader_id)
    if project_type:
        query = query.where(ResearchProject.project_type == project_type)
    if status:
        query = query.where(ResearchProject.status == status)

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    projects = result.scalars().all()

    items = [
        {
            "id": str(p.id),
            "leader_id": str(p.leader_id),
            "project_no": p.project_no,
            "title": p.title,
            "project_type": p.project_type,
            "status": p.status,
            "start_date": p.start_date.isoformat() if p.start_date else None,
            "end_date": p.end_date.isoformat() if p.end_date else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in projects
    ]

    return page_response(items, total, page, page_size)


@router.get("/{project_id}", response_model=dict)
async def get_research_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教研课题详情"""
    result = await db.execute(
        select(ResearchProject).where(ResearchProject.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        return success(None)

    return success(
        {
            "id": str(project.id),
            "leader_id": str(project.leader_id),
            "project_no": project.project_no,
            "title": project.title,
            "project_type": project.project_type,
            "background": project.background,
            "objectives": project.objectives,
            "content": project.content,
            "methods": project.methods,
            "expected_results": project.expected_results,
            "funding": project.funding,
            "start_date": project.start_date.isoformat()
            if project.start_date
            else None,
            "end_date": project.end_date.isoformat() if project.end_date else None,
            "status": project.status,
            "reviewer_id": str(project.reviewer_id) if project.reviewer_id else None,
            "reviewed_at": project.reviewed_at.isoformat()
            if project.reviewed_at
            else None,
            "review_comment": project.review_comment,
            "members": project.members,
            "attachments": project.attachments,
            "remarks": project.remarks,
        }
    )


@router.post("", response_model=dict)
async def create_research_project(
    data: ResearchProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建教研课题"""
    project = ResearchProject(**data.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return success({"id": str(project.id)}, "教研课题创建成功")


@router.put("/{project_id}", response_model=dict)
async def update_research_project(
    project_id: UUID,
    data: ResearchProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新教研课题"""
    result = await db.execute(
        select(ResearchProject).where(ResearchProject.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        return success(message="教研课题不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    await db.commit()
    await db.refresh(project)
    return success({"id": str(project.id)}, "教研课题更新成功")


@router.delete("/{project_id}", response_model=dict)
async def delete_research_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除教研课题"""
    result = await db.execute(
        select(ResearchProject).where(ResearchProject.id == project_id)
    )
    project = result.scalar_one_or_none()

    if project:
        await db.delete(project)
        await db.commit()

    return success(message="教研课题删除成功")


@router.post("/{project_id}/submit", response_model=dict)
async def submit_research_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交教研课题"""
    result = await db.execute(
        select(ResearchProject).where(ResearchProject.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        return success(message="教研课题不存在")

    project.status = "submitted"
    await db.commit()
    return success(message="教研课题提交成功")


@router.post("/{project_id}/approve", response_model=dict)
async def approve_research_project(
    project_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """审批教研课题"""
    result = await db.execute(
        select(ResearchProject).where(ResearchProject.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        return success(message="教研课题不存在")

    approve = data.get("approve", True)
    if approve:
        project.status = "approved"
        project.reviewer_id = current_user.id
        project.reviewed_at = datetime.now()
        if "comment" in data:
            project.review_comment = data["comment"]
    else:
        project.status = "rejected"
        if "comment" in data:
            project.review_comment = data["comment"]

    await db.commit()
    return success(message="教研课题审批完成")


@router.post("/{project_id}/complete", response_model=dict)
async def complete_research_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """结题教研课题"""
    result = await db.execute(
        select(ResearchProject).where(ResearchProject.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        return success(message="教研课题不存在")

    project.status = "completed"
    await db.commit()
    return success(message="教研课题结题成功")
