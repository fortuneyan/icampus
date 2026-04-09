"""
排课服务
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import Schedule
from app.core.exceptions import NotFoundException, ConflictException
from app.services.base_service import BaseService


class ScheduleService(BaseService[Schedule]):
    """排课服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(Schedule, db)

    async def create_schedule(self, data: dict) -> Schedule:
        """创建排课"""
        conflict = await self._check_conflict(
            data["class_id"],
            data["weekday"],
            data["period_start"],
            data["period_end"],
            data["semester"],
        )
        if conflict:
            raise ConflictException("该时段已有课程安排")

        return await self.create(data)

    async def update_schedule(self, schedule_id: UUID, data: dict) -> Schedule:
        """更新排课"""
        schedule = await self.get(schedule_id)
        if not schedule:
            raise NotFoundException("排课不存在")

        return await self.update(schedule_id, data)

    async def _check_conflict(
        self,
        class_id: UUID,
        weekday: int,
        period_start: int,
        period_end: int,
        semester: str,
    ) -> Optional[Schedule]:
        """检查时间冲突"""
        schedules = await self.get_all(
            [
                Schedule.class_id == class_id,
                Schedule.weekday == weekday,
                Schedule.semester == semester,
            ]
        )

        for s in schedules:
            if not (period_end < s.period_start or period_start > s.period_end):
                return s
        return None

    async def get_class_schedule(
        self, class_id: UUID, semester: Optional[str] = None
    ) -> List[Schedule]:
        """获取班级课表"""
        filters = [Schedule.class_id == class_id]
        if semester:
            filters.append(Schedule.semester == semester)

        return await self.get_all(filters)

    async def get_teacher_schedule(
        self, teacher_id: UUID, semester: Optional[str] = None
    ) -> List[Schedule]:
        """获取教师课表"""
        filters = [Schedule.teacher_id == teacher_id]
        if semester:
            filters.append(Schedule.semester == semester)

        return await self.get_all(filters)

    async def get_schedule_by_class(
        self, class_id: UUID, weekday: int, semester: str
    ) -> List[Schedule]:
        """获取班级某天课表"""
        return await self.get_all(
            [
                Schedule.class_id == class_id,
                Schedule.weekday == weekday,
                Schedule.semester == semester,
            ]
        )

    async def delete_schedule(self, schedule_id: UUID) -> bool:
        """删除排课"""
        schedule = await self.get(schedule_id)
        if not schedule:
            raise NotFoundException("排课不存在")

        return await self.delete(schedule_id) is not None
