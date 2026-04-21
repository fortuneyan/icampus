from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import csv
import io

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.recruitment import RecruitmentPlan, Applicant
from app.schemas.recruitment import (
    RecruitmentPlanCreate, RecruitmentPlanUpdate,
    ApplicantCreate, ApplicantUpdate, ApplicantBatchUpdate, FollowUpCreate
)
from app.schemas.response import success, page_response
from app.services.recruitment_service import RecruitmentService, ApplicantService, FollowUpService

router = APIRouter()

CSV_REQUIRED_HEADERS = ["student_name", "phone"]
CSV_OPTIONAL_HEADERS = ["gender", "birth_date", "guardian_name", "guardian_phone", "id_card", "address", "current_school", "source", "remarks"]


@router.get("/plans", response_model=dict)
async def get_recruitment_plans(
    year: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RecruitmentService(db)
    query = select(RecruitmentPlan).order_by(RecruitmentPlan.created_at.desc())
    
    if year:
        query = query.where(RecruitmentPlan.year == year)
    if status:
        query = query.where(RecruitmentPlan.status == status)
    
    result = await db.execute(query)
    plans = result.scalars().all()
    
    total = len(plans)
    offset = (page - 1) * page_size
    items = plans[offset:offset + page_size]
    
    return page_response([
        {
            "id": str(p.id),
            "name": p.name,
            "year": p.year,
            "grade_id": str(p.grade_id) if p.grade_id else None,
            "quota": p.quota,
            "start_date": p.start_date.isoformat(),
            "end_date": p.end_date.isoformat(),
            "description": p.description,
            "status": p.status,
            "created_at": p.created_at.isoformat(),
        }
        for p in items
    ], total, page, page_size)


@router.post("/plans", response_model=dict)
async def create_recruitment_plan(
    data: RecruitmentPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RecruitmentService(db)
    plan = await service.create(data.model_dump())
    return success({"id": str(plan.id)}, "招生计划创建成功")


@router.put("/plans/{plan_id}", response_model=dict)
async def update_recruitment_plan(
    plan_id: UUID,
    data: RecruitmentPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RecruitmentService(db)
    plan = await service.get(plan_id)
    if not plan:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("招生计划不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)
    
    await db.commit()
    await db.refresh(plan)
    return success({"id": str(plan.id)}, "招生计划更新成功")


@router.put("/plans/{plan_id}/status", response_model=dict)
async def change_plan_status(
    plan_id: UUID,
    status: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    valid_statuses = ["draft", "published", "recruiting", "closed"]
    if status not in valid_statuses:
        from app.core.exceptions import ValidationException
        raise ValidationException(f"无效的状态: {status}")
    
    result = await db.execute(select(RecruitmentPlan).where(RecruitmentPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    
    if not plan:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("招生计划不存在")
    
    plan.status = status
    await db.commit()
    await db.refresh(plan)
    
    return success({"id": str(plan.id), "status": plan.status}, "状态更新成功")


@router.post("/plans/{plan_id}/publish", response_model=dict)
async def publish_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import update
    from app.models.notification import Notification
    
    result = await db.execute(select(RecruitmentPlan).where(RecruitmentPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    
    if not plan:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("招生计划不存在")
    
    notification = Notification(
        title=f"招生公告: {plan.name}",
        content=plan.description or "",
        notification_type="announcement",
        sender_id=current_user.id,
        scope_type="all",
        status="published",
    )
    db.add(notification)
    await db.flush()
    
    plan.status = "published"
    plan.is_public = True
    plan.announcement_id = notification.id
    await db.commit()
    await db.refresh(plan)
    
    return success({"id": str(plan.id), "notification_id": str(notification.id)}, "发布成功")


@router.post("/plans/{plan_id}/close", response_model=dict)
async def close_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(RecruitmentPlan).where(RecruitmentPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    
    if not plan:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("招生计划不存在")
    
    plan.status = "closed"
    await db.commit()
    await db.refresh(plan)
    
    return success({"id": str(plan.id)}, "招生计划已关闭")


@router.get("/applicants", response_model=dict)
async def get_applicants(
    status: Optional[str] = Query(None),
    recruitment_plan_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ApplicantService(db)
    query = select(Applicant).order_by(Applicant.created_at.desc())
    
    if status:
        query = query.where(Applicant.status == status)
    if recruitment_plan_id:
        query = query.where(Applicant.recruitment_plan_id == UUID(recruitment_plan_id))
    
    result = await db.execute(query)
    applicants = result.scalars().all()
    
    total = len(applicants)
    offset = (page - 1) * page_size
    items = applicants[offset:offset + page_size]
    
    return page_response([
        {
            "id": str(a.id),
            "student_name": a.student_name,
            "gender": a.gender,
            "phone": a.phone,
            "guardian_name": a.guardian_name,
            "source": a.source,
            "status": a.status,
            "is_enrolled": a.is_enrolled,
            "created_at": a.created_at.isoformat(),
        }
        for a in items
    ], total, page, page_size)


@router.post("/applicants", response_model=dict)
async def create_applicant(
    data: ApplicantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ApplicantService(db)
    
    existing = await service.get_by_phone(data.phone)
    if existing:
        from app.core.exceptions import ConflictException
        raise ConflictException("该手机号已报名")
    
    applicant = await service.create(data.model_dump())
    return success({"id": str(applicant.id)}, "报名信息提交成功")


@router.put("/applicants/{applicant_id}/status", response_model=dict)
async def update_applicant_status(
    applicant_id: UUID,
    status: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ApplicantService(db)
    applicant = await service.update_status(applicant_id, status)
    
    if not applicant:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("报名信息不存在")
    
    return success(message="状态更新成功")


@router.post("/applicants/{applicant_id}/follow-up", response_model=dict)
async def add_follow_up(
    applicant_id: UUID,
    data: FollowUpCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FollowUpService(db)
    follow_up = await service.add_follow_up(applicant_id, current_user.id, data.model_dump())
    return success({"id": str(follow_up.id)}, "跟进记录添加成功")


@router.get("/applicants/{applicant_id}/follow-ups", response_model=dict)
async def get_follow_ups(
    applicant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FollowUpService(db)
    follow_ups = await service.get_by_applicant(applicant_id)
    
    return success([
        {
            "id": str(f.id),
            "follow_type": f.follow_type,
            "content": f.content,
            "next_follow_date": f.next_follow_date.isoformat() if f.next_follow_date else None,
            "created_at": f.created_at.isoformat(),
        }
        for f in follow_ups
    ])


@router.get("/stats", response_model=dict)
async def get_recruitment_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.recruitment import Applicant
    
    pending_result = await db.execute(
        select(func.count()).select_from(Applicant).where(Applicant.status == "pending")
    )
    contacted_result = await db.execute(
        select(func.count()).select_from(Applicant).where(Applicant.status == "contacted")
    )
    interviewed_result = await db.execute(
        select(func.count()).select_from(Applicant).where(Applicant.status == "interviewed")
    )
    admitted_result = await db.execute(
        select(func.count()).select_from(Applicant).where(Applicant.status == "admitted")
    )
    
    return success({
        "pending": pending_result.scalar(),
        "contacted": contacted_result.scalar(),
        "interviewed": interviewed_result.scalar(),
        "admitted": admitted_result.scalar(),
    })


@router.put("/applicants/batch", response_model=dict)
async def batch_update_applicants(
    data: ApplicantBatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not data.ids:
        from app.core.exceptions import ValidationException
        raise ValidationException("请选择要更新的记录")
    
    from sqlalchemy import update
    from app.models.recruitment import Applicant
    
    update_data = {}
    if data.status:
        update_data["status"] = data.status
    if data.enrollment_batch:
        update_data["enrollment_batch"] = data.enrollment_batch
    if data.recruitment_plan_id:
        update_data["recruitment_plan_id"] = UUID(data.recruitment_plan_id)
    
    if not update_data:
        from app.core.exceptions import ValidationException
        raise ValidationException("请提供要更新的字段")
    
    stmt = (
        update(Applicant)
        .where(Applicant.id.in_([UUID(id) for id in data.ids]))
        .values(**update_data)
    )
    await db.execute(stmt)
    await db.commit()
    
    return success({"updated": len(data.ids)}, f"成功更新{len(data.ids)}条记录")


@router.get("/plans/{plan_id}/public", response_model=dict)
async def get_public_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RecruitmentPlan).where(RecruitmentPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("招生计划不存在")
    
    return success({
        "id": str(plan.id),
        "name": plan.name,
        "year": plan.year,
        "quota": plan.quota,
        "tuition": float(plan.tuition) if plan.tuition else 0,
        "start_date": plan.start_date.isoformat(),
        "end_date": plan.end_date.isoformat(),
        "description": plan.description,
        "requirements": plan.requirements,
    })


@router.post("/apply/public", response_model=dict)
async def public_apply(
    student_name: str = Form(...),
    gender: Optional[str] = Form(None),
    birth_date: Optional[str] = Form(None),
    phone: str = Form(...),
    guardian_name: Optional[str] = Form(None),
    guardian_phone: Optional[str] = Form(None),
    id_card: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    current_school: Optional[str] = Form(None),
    source: Optional[str] = Form("online"),
    recruitment_plan_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    from app.models.recruitment import RecruitmentPlan, Applicant
    from app.models.recruitment import Applicant
    
    existing = await db.execute(
        select(Applicant).where(Applicant.phone == phone)
    )
    if existing.scalar_one_or_none():
        from app.core.exceptions import ConflictException
        raise ConflictException("该手机号已报名，请勿重复提交")
    
    plan_id = None
    is_off_plan = False
    
    if recruitment_plan_id:
        plan_id = UUID(recruitment_plan_id)
    else:
        active_plan_result = await db.execute(
            select(RecruitmentPlan)
            .where(RecruitmentPlan.status == "recruiting")
            .where(RecruitmentPlan.start_date <= datetime.now())
            .where(RecruitmentPlan.end_date >= datetime.now())
            .order_by(RecruitmentPlan.quota - RecruitmentPlan.enrolled_count)
            .limit(1)
        )
        active_plan = active_plan_result.scalar_one_or_none()
        if active_plan:
            plan_id = active_plan.id
        else:
            is_off_plan = True
    
    applicant_data = {
        "student_name": student_name,
        "gender": gender,
        "phone": phone,
        "guardian_name": guardian_name,
        "guardian_phone": guardian_phone,
        "id_card": id_card,
        "address": address,
        "current_school": current_school,
        "source": source or "online",
        "recruitment_plan_id": plan_id,
    }
    
    if birth_date:
        try:
            applicant_data["birth_date"] = datetime.fromisoformat(birth_date)
        except:
            pass
    
    applicant = Applicant(**applicant_data)
    db.add(applicant)
    
    if plan_id:
        plan_result = await db.execute(select(RecruitmentPlan).where(RecruitmentPlan.id == plan_id))
        plan = plan_result.scalar_one_or_none()
        if plan:
            plan.enrolled_count = (plan.enrolled_count or 0) + 1
    
    await db.commit()
    await db.refresh(applicant)
    
    msg = "报名信息提交成功"
    if is_off_plan:
        msg += "（计划外招生）"
    
    return success({"id": str(applicant.id), "is_off_plan": is_off_plan}, msg)


@router.get("/apply/status", response_model=dict)
async def check_application_status(
    phone: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Applicant).where(Applicant.phone == phone)
    )
    applicant = result.scalar_one_or_none()
    
    if not applicant:
        return success({"status": "not_found"}, "未找到报名信息")
    
    return success({
        "status": applicant.status,
        "student_name": applicant.student_name,
        "enrollment_batch": applicant.enrollment_batch,
    })


def parse_csv_row(row: dict, headers: list) -> dict:
    """解析CSV行数据"""
    data = {}
    for key in CSV_REQUIRED_HEADERS + CSV_OPTIONAL_HEADERS:
        if key in headers:
            value = row.get(key, "").strip()
            if value:
                if key == "birth_date":
                    try:
                        data[key] = datetime.strptime(value, "%Y-%m-%d")
                    except:
                        try:
                            data[key] = datetime.strptime(value, "%Y/%m/%d")
                        except:
                            data[key] = None
                else:
                    data[key] = value
    return data


@router.post("/applicants/import", response_model=dict)
async def import_applicants(
    file: UploadFile = File(...),
    recruitment_plan_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    filename = file.filename.lower()
    
    success_count = 0
    fail_count = 0
    errors = []
    
    try:
        if filename.endswith(".csv"):
            decoded = content.decode("utf-8")
            reader = csv.DictReader(io.StringIO(decoded))
            headers = reader.fieldnames or []
            
            if not headers:
                from app.core.exceptions import ValidationException
                raise ValidationException("CSV文件 headers 为空")
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    row_data = parse_csv_row(row, headers)
                    if not row_data.get("student_name") or not row_data.get("phone"):
                        fail_count += 1
                        errors.append(f"第{row_num}行: 必填字段缺失")
                        continue
                    
                    existing = await db.execute(
                        select(Applicant).where(Applicant.phone == row_data["phone"])
                    )
                    if existing.scalar_one_or_none():
                        fail_count += 1
                        errors.append(f"第{row_num}行: 手机号 {row_data['phone']} 已存在")
                        continue
                    
                    if recruitment_plan_id:
                        row_data["recruitment_plan_id"] = UUID(recruitment_plan_id)
                    
                    applicant = Applicant(**row_data)
                    db.add(applicant)
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    errors.append(f"第{row_num}行: {str(e)}")
        
        elif filename.endswith((".xls", ".xlsx")):
            from app.core.exceptions import NotImplementedException
            raise NotImplementedException("EXCEL导入功能开发中，请先导出CSV模板")
        else:
            from app.core.exceptions import ValidationException
            raise ValidationException("仅支持CSV文件格式")
        
        await db.commit()
        
        return success({
            "success_count": success_count,
            "fail_count": fail_count,
            "errors": errors[:100],
        }, f"导入完成: 成功{success_count}条, 失败{fail_count}条")
    
    except Exception as e:
        await db.rollback()
        raise


@router.get("/applicants/template", response_model=dict)
async def download_template(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    headers = CSV_REQUIRED_HEADERS + CSV_OPTIONAL_HEADERS
    csv_content = ",".join(headers) + "\n"
    csv_content += "张三,13800138000,男,2015-01-01,张父,13900139000,110101201501010001,北京市朝阳区,北京市第一小学,转介绍,无\n"
    csv_content += "李四,13900139001,,,李母,,,,,,,\n"
    
    from fastapi.responses import Response
    return Response(
        content=csv_content.encode("utf-8"),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=报名信息导入模板.csv"},
    )
