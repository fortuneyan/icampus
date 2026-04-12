"""
宿舍管理接口
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.dormitory import Dormitory, DormitoryRoom, DormitoryAssignment, DormitoryAttendance
from app.schemas.response import success, page_response

router = APIRouter()


# ==================== 宿舍楼栋 ====================

class DormitoryCreate(BaseModel):
    name: str
    building_no: str
    floor_count: int = 1
    building_type: str = "female"
    remarks: Optional[str] = None


@router.get("/buildings", response_model=dict)
async def get_dormitories(
    keyword: Optional[str] = Query(None),
    building_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取宿舍楼栋列表"""
    query = select(Dormitory).order_by(desc(Dormitory.created_at))
    
    if keyword:
        query = query.where(Dormitory.name.ilike(f"%{keyword}%"))
    if building_type:
        query = query.where(Dormitory.building_type == building_type)
    if status:
        query = query.where(Dormitory.status == status)
    
    total_result = await db.execute(query)
    total = len(total_result.scalars().all())
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return page_response([
        {
            "id": str(d.id),
            "name": d.name,
            "building_no": d.building_no,
            "floor_count": d.floor_count,
            "building_type": d.building_type,
            "status": d.status,
            "remarks": d.remarks,
        }
        for d in items
    ], total, page, page_size)


@router.post("/buildings", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_dormitory(
    data: DormitoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建宿舍楼栋"""
    dorm = Dormitory(**data.model_dump())
    db.add(dorm)
    await db.commit()
    await db.refresh(dorm)
    return success({"id": str(dorm.id)}, "创建成功")


# ==================== 宿舍房间 ====================

class RoomCreate(BaseModel):
    dormitory_id: UUID
    room_no: str
    floor: int
    bed_count: int = 4
    room_type: str = "standard"


@router.get("/rooms", response_model=dict)
async def get_rooms(
    dormitory_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取宿舍房间列表"""
    query = select(DormitoryRoom).order_by(desc(DormitoryRoom.created_at))
    
    if dormitory_id:
        query = query.where(DormitoryRoom.dormitory_id == dormitory_id)
    if status:
        query = query.where(DormitoryRoom.status == status)
    
    total_result = await db.execute(query)
    total = len(total_result.scalars().all())
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return page_response([
        {
            "id": str(r.id),
            "dormitory_id": str(r.dormitory_id),
            "room_no": r.room_no,
            "floor": r.floor,
            "bed_count": r.bed_count,
            "occupied_beds": r.occupied_beds,
            "room_type": r.room_type,
            "status": r.status,
        }
        for r in items
    ], total, page, page_size)


@router.post("/rooms", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_room(
    data: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建宿舍房间"""
    room = DormitoryRoom(**data.model_dump())
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return success({"id": str(room.id)}, "创建成功")


# ==================== 住宿分配 ====================

class AssignmentCreate(BaseModel):
    student_id: UUID
    room_id: UUID
    bed_no: int
    academic_year: str
    semester: str


@router.get("/assignments", response_model=dict)
async def get_assignments(
    student_id: Optional[UUID] = Query(None),
    academic_year: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取住宿分配列表"""
    query = select(DormitoryAssignment).order_by(desc(DormitoryAssignment.created_at))
    
    if student_id:
        query = query.where(DormitoryAssignment.student_id == student_id)
    if academic_year:
        query = query.where(DormitoryAssignment.academic_year == academic_year)
    
    total_result = await db.execute(query)
    total = len(total_result.scalars().all())
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return page_response([
        {
            "id": str(a.id),
            "student_id": str(a.student_id),
            "room_id": str(a.room_id),
            "bed_no": a.bed_no,
            "academic_year": a.academic_year,
            "semester": a.semester,
            "status": a.status,
        }
        for a in items
    ], total, page, page_size)


@router.post("/assignments", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    data: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建住宿分配"""
    assignment = DormitoryAssignment(**data.model_dump())
    db.add(assignment)
    
    # 更新房间已占用床位
    room_result = await db.execute(
        select(DormitoryRoom).where(DormitoryRoom.id == data.room_id)
    )
    room = room_result.scalar_one_or_none()
    if room:
        room.occupied_beds += 1
    
    await db.commit()
    await db.refresh(assignment)
    return success({"id": str(assignment.id)}, "分配成功")
