"""
考勤服务
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceRule, AttendanceRecord
from app.core.exceptions import NotFoundException
from app.services.base_service import BaseService


class RuleService(BaseService[AttendanceRule]):
    """考勤规则服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(AttendanceRule, db)

    async def create_rule(self, data: dict) -> AttendanceRule:
        return await self.create(data)


class RecordService:
    """考勤记录服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_in(
        self,
        user_id: UUID,
        rule_id: Optional[UUID] = None,
        photo: Optional[str] = None,
        location: Optional[str] = None,
    ) -> AttendanceRecord:
        record = AttendanceRecord(
            user_id=user_id,
            rule_id=rule_id,
            check_in_time=datetime.now(),
            check_in_photo=photo,
            check_in_location=location,
            status="normal",
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def check_out(self, record_id: UUID) -> Optional[AttendanceRecord]:
        record = await self.db.get(AttendanceRecord, record_id)
        if record:
            record.check_out_time = datetime.now()
            await self.db.commit()
            await self.db.refresh(record)
        return record

    async def get_user_records(
        self, user_id: UUID, page: int = 1, page_size: int = 20
    ) -> dict:
        query = (
            select(AttendanceRecord)
            .where(AttendanceRecord.user_id == user_id)
            .order_by(AttendanceRecord.created_at.desc())
        )
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count())
            .select_from(AttendanceRecord)
            .where(AttendanceRecord.user_id == user_id)
        )
        total = count_result.scalar()

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    async def get_statistics(
        self, user_id: UUID, start_date: datetime, end_date: datetime
    ) -> dict:
        result = await self.db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.user_id == user_id,
                AttendanceRecord.created_at >= start_date,
                AttendanceRecord.created_at <= end_date,
            )
        )
        records = list(result.scalars().all())

        total = len(records)
        normal = len([r for r in records if r.status == "normal"])
        late = len([r for r in records if r.status == "late"])

        return {
            "total": total,
            "normal": normal,
            "late": late,
            "absence": 0,
            "rate": round(normal / total * 100, 2) if total > 0 else 0,
        }
