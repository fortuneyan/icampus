"""
智能排课服务 - 数据库持久化版本

基于sch_数据库表的完整排课服务
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.scheduling_models import (
    SchCycle, SchSemester, SchCalendarMap, SchTemplate, SchPeriod,
    SchPlan, SchResult, SchPatch, SchConstraint, SchEvent,
    SchPlanTeacherReplace
)
from app.models.schedule import Classroom
from app.models.course import Course
from app.models.class_model import Class
from app.models.user import User
from app.schemas.scheduling import (
    SemesterCreate, CycleCreate, CalendarMapCreate, TemplateCreate,
    PeriodCreate, PlanCreate, ResultCreate, PatchCreate,
    ConstraintCreate, EventCreate, ReplaceCreate,
    ScheduleCell, DaySchedule, ClassScheduleResponse, ConflictInfo,
    DragAdjustRequest, OptimizationResult as OptResult
)


class SchedulingDBService:
    """
    智能排课数据库服务

    提供完整的数据库持久化排课功能：
    - 学期和周次管理
    - 课程规划管理
    - 排课结果管理
    - 临时调课管理
    - 冲突检测
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============ 学期管理 ============

    async def create_semester(self, data: SemesterCreate) -> SchSemester:
        """创建学期"""
        semester = SchSemester(
            id=data.academic_year.replace("-", "") + ("01" if data.semester == 1 else "02"),
            name=data.name,
            academic_year=data.academic_year,
            semester=data.semester,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        self.db.add(semester)
        await self.db.commit()
        await self.db.refresh(semester)
        return semester

    async def get_semesters(self, status: Optional[str] = None) -> List[SchSemester]:
        """获取学期列表"""
        query = select(SchSemester)
        if status:
            query = query.where(SchSemester.status == status)
        query = query.order_by(SchSemester.academic_year.desc(), SchSemester.semester)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_semester(self, semester_id: str) -> Optional[SchSemester]:
        """获取学期详情"""
        result = await self.db.execute(
            select(SchSemester).where(SchSemester.id == semester_id)
        )
        return result.scalar_one_or_none()

    # ============ 周次组合管理 ============

    async def create_cycle(self, data: CycleCreate) -> SchCycle:
        """创建周次组合"""
        cycle = SchCycle(
            id=data.id,
            semester_id=data.semester_id,
            start_date=data.start_date,
            end_date=data.end_date,
            cycle_type=data.cycle_type,
        )
        self.db.add(cycle)
        await self.db.commit()
        await self.db.refresh(cycle)
        return cycle

    async def get_cycles(self, semester_id: Optional[str] = None) -> List[SchCycle]:
        """获取周次组合列表"""
        query = select(SchCycle)
        if semester_id:
            query = query.where(SchCycle.semester_id == semester_id)
        query = query.order_by(SchCycle.start_date)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_current_cycle(self, semester_id: str) -> Optional[SchCycle]:
        """获取当前生效的周次组合"""
        result = await self.db.execute(
            select(SchCycle).where(
                and_(SchCycle.semester_id == semester_id, SchCycle.is_current == True)
            )
        )
        return result.scalar_one_or_none()

    async def set_current_cycle(self, cycle_id: str) -> None:
        """设置当前生效的周次组合"""
        # 先取消所有当前生效
        cycle = await self.db.execute(
            select(SchCycle).where(SchCycle.id == cycle_id)
        )
        cycle_obj = cycle.scalar_one_or_none()
        if not cycle_obj:
            return

        semester_id = cycle_obj.semester_id
        await self.db.execute(
            select(SchCycle).where(SchCycle.semester_id == semester_id).with_for_update()
        )

        # 取消所有当前
        result = await self.db.execute(
            select(SchCycle).where(SchCycle.semester_id == semester_id)
        )
        for c in result.scalars():
            c.is_current = False

        # 设置新的当前
        cycle_obj.is_current = True
        await self.db.commit()

    # ============ 日历映射管理 ============

    async def create_calendar_map(self, data: CalendarMapCreate) -> SchCalendarMap:
        """创建日历映射"""
        calendar_map = SchCalendarMap(
            natural_date=data.natural_date,
            cycle_id=data.cycle_id,
            exec_day=data.exec_day,
            is_workday=data.is_workday,
            is_holiday=data.is_holiday,
        )
        self.db.add(calendar_map)
        await self.db.commit()
        await self.db.refresh(calendar_map)
        return calendar_map

    async def batch_create_calendar_maps(self, items: List[CalendarMapCreate]) -> List[SchCalendarMap]:
        """批量创建日历映射"""
        calendar_maps = []
        for item in items:
            calendar_map = SchCalendarMap(
                natural_date=item.natural_date,
                cycle_id=item.cycle_id,
                exec_day=item.exec_day,
                is_workday=item.is_workday,
                is_holiday=item.is_holiday,
            )
            self.db.add(calendar_map)
            calendar_maps.append(calendar_map)
        await self.db.commit()
        for cm in calendar_maps:
            await self.db.refresh(cm)
        return calendar_maps

    async def get_calendar_map(self, natural_date: date) -> Optional[SchCalendarMap]:
        """获取指定日期的日历映射"""
        result = await self.db.execute(
            select(SchCalendarMap).where(SchCalendarMap.natural_date == natural_date)
        )
        return result.scalar_one_or_none()

    async def get_calendar_maps(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        is_holiday: Optional[bool] = None
    ) -> List[SchCalendarMap]:
        """获取日历映射列表"""
        query = select(SchCalendarMap)
        if start_date:
            query = query.where(SchCalendarMap.natural_date >= start_date)
        if end_date:
            query = query.where(SchCalendarMap.natural_date <= end_date)
        if is_holiday is not None:
            query = query.where(SchCalendarMap.is_holiday == is_holiday)
        query = query.order_by(SchCalendarMap.natural_date)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_calendar_map(
        self,
        natural_date: date,
        cycle_id: Optional[str] = None,
        exec_day: Optional[int] = None,
        is_workday: Optional[bool] = None,
        is_holiday: Optional[bool] = None
    ) -> Optional[SchCalendarMap]:
        """更新日历映射"""
        result = await self.db.execute(
            select(SchCalendarMap).where(SchCalendarMap.natural_date == natural_date)
        )
        calendar_map = result.scalar_one_or_none()
        if not calendar_map:
            return None

        if cycle_id is not None:
            calendar_map.cycle_id = cycle_id
        if exec_day is not None:
            calendar_map.exec_day = exec_day
        if is_workday is not None:
            calendar_map.is_workday = is_workday
        if is_holiday is not None:
            calendar_map.is_holiday = is_holiday

        await self.db.commit()
        await self.db.refresh(calendar_map)
        return calendar_map

    # ============ 课表模板管理 ============

    async def create_template(self, data: TemplateCreate) -> SchTemplate:
        """创建课表模板"""
        template = SchTemplate(
            semester_id=data.semester_id,
            name=data.name,
            template_type=data.template_type,
            start_date=data.start_date,
            end_date=data.end_date,
            priority=data.priority,
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def get_templates(self, semester_id: str) -> List[SchTemplate]:
        """获取课表模板列表"""
        result = await self.db.execute(
            select(SchTemplate)
            .where(SchTemplate.semester_id == semester_id)
            .order_by(SchTemplate.priority.desc())
        )
        return list(result.scalars().all())

    async def create_period(self, data: PeriodCreate) -> SchPeriod:
        """创建节次"""
        period = SchPeriod(
            template_id=data.template_id,
            period_index=data.period_index,
            start_time=data.start_time,
            end_time=data.end_time,
            period_type=data.period_type,
            duration=data.duration,
        )
        self.db.add(period)
        await self.db.commit()
        await self.db.refresh(period)
        return period

    async def get_periods(self, template_id: UUID) -> List[SchPeriod]:
        """获取模板的节次列表"""
        result = await self.db.execute(
            select(SchPeriod)
            .where(SchPeriod.template_id == template_id)
            .order_by(SchPeriod.period_index)
        )
        return list(result.scalars().all())

    # ============ 课程规划管理 ============

    async def create_plan(self, data: PlanCreate) -> SchPlan:
        """创建课程规划"""
        plan = SchPlan(
            cycle_id=data.cycle_id,
            class_id=data.class_id,
            teacher_id=data.teacher_id,
            course_id=data.course_id,
            total_hours=data.total_hours,
            is_continuous=data.is_continuous,
            continuous_length=data.continuous_length,
            priority=data.priority,
        )
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def batch_create_plans(self, items: List[PlanCreate]) -> List[SchPlan]:
        """批量创建课程规划"""
        plans = []
        for item in items:
            plan = SchPlan(
                cycle_id=item.cycle_id,
                class_id=item.class_id,
                teacher_id=item.teacher_id,
                course_id=item.course_id,
                total_hours=item.total_hours,
                is_continuous=item.is_continuous,
                continuous_length=item.continuous_length,
                priority=item.priority,
            )
            self.db.add(plan)
            plans.append(plan)
        await self.db.commit()
        for p in plans:
            await self.db.refresh(p)
        return plans

    async def get_plans(
        self,
        cycle_id: Optional[str] = None,
        class_id: Optional[UUID] = None,
        teacher_id: Optional[UUID] = None
    ) -> List[SchPlan]:
        """获取课程规划列表"""
        query = select(SchPlan)
        if cycle_id:
            query = query.where(SchPlan.cycle_id == cycle_id)
        if class_id:
            query = query.where(SchPlan.class_id == class_id)
        if teacher_id:
            query = query.where(SchPlan.teacher_id == teacher_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ============ 排课结果管理 ============

    async def create_result(self, data: ResultCreate) -> SchResult:
        """创建排课结果"""
        result = SchResult(
            cycle_id=data.cycle_id,
            class_id=data.class_id,
            teacher_id=data.teacher_id,
            course_id=data.course_id,
            room_id=data.room_id,
            day_index=data.day_index,
            period_index=data.period_index,
            week_start=data.week_start,
            week_end=data.week_end,
            is_locked=data.is_locked,
            create_type=data.create_type,
            template_id=data.template_id,
        )
        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)
        return result

    async def batch_create_results(self, items: List[ResultCreate]) -> List[SchResult]:
        """批量创建排课结果"""
        results = []
        for item in items:
            result = SchResult(
                cycle_id=item.cycle_id,
                class_id=item.class_id,
                teacher_id=item.teacher_id,
                course_id=item.course_id,
                room_id=item.room_id,
                day_index=item.day_index,
                period_index=item.period_index,
                week_start=item.week_start,
                week_end=item.week_end,
                is_locked=item.is_locked,
                create_type=item.create_type,
                template_id=item.template_id,
            )
            self.db.add(result)
            results.append(result)
        await self.db.commit()
        for r in results:
            await self.db.refresh(r)
        return results

    async def get_results(
        self,
        cycle_id: Optional[str] = None,
        class_id: Optional[UUID] = None,
        teacher_id: Optional[UUID] = None,
        day_index: Optional[int] = None
    ) -> List[SchResult]:
        """获取排课结果列表"""
        query = select(SchResult)
        if cycle_id:
            query = query.where(SchResult.cycle_id == cycle_id)
        if class_id:
            query = query.where(SchResult.class_id == class_id)
        if teacher_id:
            query = query.where(SchResult.teacher_id == teacher_id)
        if day_index:
            query = query.where(SchResult.day_index == day_index)
        query = query.order_by(SchResult.day_index, SchResult.period_index)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_result(
        self,
        result_id: UUID,
        day_index: Optional[int] = None,
        period_index: Optional[int] = None,
        is_locked: Optional[bool] = None
    ) -> Optional[SchResult]:
        """更新排课结果"""
        result = await self.db.execute(
            select(SchResult).where(SchResult.id == result_id)
        )
        result_obj = result.scalar_one_or_none()
        if not result_obj:
            return None

        if day_index is not None:
            result_obj.day_index = day_index
        if period_index is not None:
            result_obj.period_index = period_index
        if is_locked is not None:
            result_obj.is_locked = is_locked

        await self.db.commit()
        await self.db.refresh(result_obj)
        return result_obj

    async def delete_results_by_cycle(self, cycle_id: str, locked_only: bool = False) -> int:
        """删除周次组合的排课结果"""
        query = select(SchResult).where(SchResult.cycle_id == cycle_id)
        if locked_only:
            query = query.where(SchResult.is_locked == False)
        result = await self.db.execute(query)
        count = 0
        for r in result.scalars():
            await self.db.delete(r)
            count += 1
        await self.db.commit()
        return count

    # ============ 调课补丁管理 ============

    async def create_patch(self, data: PatchCreate) -> SchPatch:
        """创建调课补丁"""
        patch = SchPatch(
            natural_date=data.natural_date,
            class_id=data.class_id,
            day_index=data.day_index,
            period_index=data.period_index,
            original_teacher_id=data.original_teacher_id,
            patch_teacher_id=data.patch_teacher_id,
            original_course_id=data.original_course_id,
            patch_course_id=data.patch_course_id,
            original_room_id=data.original_room_id,
            patch_room_id=data.patch_room_id,
            patch_type=data.patch_type,
            reason=data.reason,
            status="active",
        )
        self.db.add(patch)
        await self.db.commit()
        await self.db.refresh(patch)
        return patch

    async def get_patches(
        self,
        natural_date: Optional[date] = None,
        class_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> List[SchPatch]:
        """获取调课补丁列表"""
        query = select(SchPatch)
        if natural_date:
            query = query.where(SchPatch.natural_date == natural_date)
        if class_id:
            query = query.where(SchPatch.class_id == class_id)
        if status:
            query = query.where(SchPatch.status == status)
        query = query.order_by(SchPatch.natural_date, SchPatch.period_index)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def cancel_patch(self, patch_id: UUID) -> Optional[SchPatch]:
        """取消调课补丁"""
        result = await self.db.execute(
            select(SchPatch).where(SchPatch.id == patch_id)
        )
        patch = result.scalar_one_or_none()
        if not patch:
            return None

        patch.status = "cancelled"
        await self.db.commit()
        await self.db.refresh(patch)
        return patch

    # ============ 冲突检测 ============

    async def check_conflicts(
        self,
        cycle_id: str,
        class_id: Optional[UUID] = None,
        teacher_id: Optional[UUID] = None
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        检测排课冲突

        Returns:
            Tuple[bool, List[Dict]]: (是否有冲突, 冲突列表)
        """
        conflicts = []

        # 获取排课结果
        query = select(SchResult).where(SchResult.cycle_id == cycle_id)
        if class_id:
            query = query.where(SchResult.class_id == class_id)
        if teacher_id:
            query = query.where(SchResult.teacher_id == teacher_id)

        result = await self.db.execute(query)
        results = list(result.scalars().all())

        # 检测教师冲突
        teacher_slots: Dict[str, List[SchResult]] = {}
        for r in results:
            key = f"{r.teacher_id}_{r.day_index}_{r.period_index}"
            if key not in teacher_slots:
                teacher_slots[key] = []
            teacher_slots[key].append(r)

        for key, items in teacher_slots.items():
            if len(items) > 1:
                conflicts.append({
                    "conflict_type": "teacher_conflict",
                    "severity": 4,
                    "message": f"教师在同一时段有多门课程",
                    "related_ids": [str(r.id) for r in items]
                })

        # 检测班级冲突
        class_slots: Dict[str, List[SchResult]] = {}
        for r in results:
            key = f"{r.class_id}_{r.day_index}_{r.period_index}"
            if key not in class_slots:
                class_slots[key] = []
            class_slots[key].append(r)

        for key, items in class_slots.items():
            if len(items) > 1:
                conflicts.append({
                    "conflict_type": "class_conflict",
                    "severity": 5,
                    "message": f"班级在同一时段有多门课程",
                    "related_ids": [str(r.id) for r in items]
                })

        # 检测教室冲突
        room_slots: Dict[str, List[SchResult]] = {}
        for r in results:
            if not r.room_id:
                continue
            key = f"{r.room_id}_{r.day_index}_{r.period_index}"
            if key not in room_slots:
                room_slots[key] = []
            room_slots[key].append(r)

        for key, items in room_slots.items():
            if len(items) > 1:
                conflicts.append({
                    "conflict_type": "room_conflict",
                    "severity": 3,
                    "message": f"教室在同一时段被多次使用",
                    "related_ids": [str(r.id) for r in items]
                })

        return len(conflicts) > 0, conflicts

    # ============ 课表查询 ============

    async def get_class_schedule(
        self,
        class_id: UUID,
        cycle_id: Optional[str] = None,
        natural_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """获取班级课表"""
        # 确定cycle_id
        if not cycle_id:
            if natural_date:
                # 从日历映射获取cycle_id
                calendar = await self.get_calendar_map(natural_date)
                if calendar:
                    cycle_id = calendar.cycle_id
            if not cycle_id:
                return {"class_id": str(class_id), "cycle_id": "", "days": []}

        # 获取排课结果
        results = await self.get_results(cycle_id=cycle_id, class_id=class_id)

        # 构建课表数据
        days = []
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for day_idx in range(1, 8):
            day_results = [r for r in results if r.day_index == day_idx]
            periods = []

            for period_idx in range(1, 11):
                result = next((r for r in day_results if r.period_index == period_idx), None)

                if result:
                    # 获取关联信息
                    course_name = ""
                    teacher_name = ""
                    room_name = ""

                    course_result = await self.db.execute(
                        select(Course).where(Course.id == result.course_id)
                    )
                    course = course_result.scalar_one_or_none()
                    if course:
                        course_name = course.name

                    teacher_result = await self.db.execute(
                        select(User).where(User.id == result.teacher_id)
                    )
                    teacher = teacher_result.scalar_one_or_none()
                    if teacher:
                        teacher_name = teacher.name

                    if result.room_id:
                        room_result = await self.db.execute(
                            select(Classroom).where(Classroom.id == result.room_id)
                        )
                        room = room_result.scalar_one_or_none()
                        if room:
                            room_name = f"{room.building or ''}{room.room_no}"

                    cell = ScheduleCell(
                        result_id=result.id,
                        course_id=result.course_id,
                        course_name=course_name,
                        teacher_id=result.teacher_id,
                        teacher_name=teacher_name,
                        room_id=result.room_id,
                        room_name=room_name,
                        is_locked=result.is_locked,
                        create_type=result.create_type,
                    )
                else:
                    cell = ScheduleCell()

                periods.append(cell)

            days.append(DaySchedule(
                day_index=day_idx,
                day_name=day_names[day_idx - 1],
                periods=periods
            ))

        # 获取班级名称
        class_result = await self.db.execute(
            select(Class).where(Class.id == class_id)
        )
        class_obj = class_result.scalar_one_or_none()
        class_name = class_obj.name if class_obj else ""

        return ClassScheduleResponse(
            class_id=class_id,
            class_name=class_name,
            cycle_id=cycle_id,
            days=days
        ).model_dump()

    async def get_teacher_schedule(
        self,
        teacher_id: UUID,
        cycle_id: Optional[str] = None,
        natural_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """获取教师课表"""
        if not cycle_id:
            if natural_date:
                calendar = await self.get_calendar_map(natural_date)
                if calendar:
                    cycle_id = calendar.cycle_id
            if not cycle_id:
                return {"teacher_id": str(teacher_id), "cycle_id": "", "days": []}

        results = await self.get_results(cycle_id=cycle_id, teacher_id=teacher_id)

        days = []
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for day_idx in range(1, 8):
            day_results = [r for r in results if r.day_index == day_idx]
            periods = []

            for period_idx in range(1, 11):
                result = next((r for r in day_results if r.period_index == period_idx), None)

                if result:
                    class_name = ""
                    course_name = ""
                    room_name = ""

                    class_result = await self.db.execute(
                        select(Class).where(Class.id == result.class_id)
                    )
                    class_obj = class_result.scalar_one_or_none()
                    if class_obj:
                        class_name = class_obj.name

                    course_result = await self.db.execute(
                        select(Course).where(Course.id == result.course_id)
                    )
                    course = course_result.scalar_one_or_none()
                    if course:
                        course_name = course.name

                    if result.room_id:
                        room_result = await self.db.execute(
                            select(Classroom).where(Classroom.id == result.room_id)
                        )
                        room = room_result.scalar_one_or_none()
                        if room:
                            room_name = f"{room.building or ''}{room.room_no}"

                    cell = ScheduleCell(
                        result_id=result.id,
                        course_id=result.course_id,
                        course_name=course_name,
                        teacher_id=result.teacher_id,
                        teacher_name=class_name,
                        room_id=result.room_id,
                        room_name=room_name,
                        is_locked=result.is_locked,
                        create_type=result.create_type,
                    )
                else:
                    cell = ScheduleCell()

                periods.append(cell)

            days.append(DaySchedule(
                day_index=day_idx,
                day_name=day_names[day_idx - 1],
                periods=periods
            ))

        teacher_result = await self.db.execute(
            select(User).where(User.id == teacher_id)
        )
        teacher = teacher_result.scalar_one_or_none()
        teacher_name = teacher.name if teacher else ""

        return {
            "teacher_id": str(teacher_id),
            "teacher_name": teacher_name,
            "cycle_id": cycle_id,
            "days": days
        }

    # ============ 拖拽调整 ============

    async def drag_adjust(self, request: DragAdjustRequest) -> Dict[str, Any]:
        """拖拽调整课程"""
        # 获取原结果
        result = await self.db.execute(
            select(SchResult).where(SchResult.id == request.result_id)
        )
        result_obj = result.scalar_one_or_none()

        if not result_obj:
            return {"success": False, "message": "排课结果不存在", "has_conflict": False, "conflicts": []}

        # 检查锁定
        if result_obj.is_locked:
            return {"success": False, "message": "该课程已锁定，无法调整", "has_conflict": False, "conflicts": []}

        # 检查新位置是否有冲突
        new_day = request.new_day_index
        new_period = request.new_period_index

        # 检查班级冲突
        class_result = await self.db.execute(
            select(SchResult).where(
                and_(
                    SchResult.cycle_id == result_obj.cycle_id,
                    SchResult.class_id == result_obj.class_id,
                    SchResult.day_index == new_day,
                    SchResult.period_index == new_period,
                    SchResult.id != request.result_id
                )
            )
        )
        if class_result.scalar_one_or_none():
            return {
                "success": False,
                "message": "班级在该时段已有课程",
                "has_conflict": True,
                "conflicts": [{
                    "conflict_type": "class_conflict",
                    "severity": 5,
                    "message": "班级在该时段已有课程"
                }]
            }

        # 检查教师冲突
        teacher_result = await self.db.execute(
            select(SchResult).where(
                and_(
                    SchResult.cycle_id == result_obj.cycle_id,
                    SchResult.teacher_id == result_obj.teacher_id,
                    SchResult.day_index == new_day,
                    SchResult.period_index == new_period,
                    SchResult.id != request.result_id
                )
            )
        )
        if teacher_result.scalar_one_or_none():
            return {
                "success": False,
                "message": "教师在该时段已有课程",
                "has_conflict": True,
                "conflicts": [{
                    "conflict_type": "teacher_conflict",
                    "severity": 4,
                    "message": "教师在该时段已有课程"
                }]
            }

        # 执行调整
        result_obj.day_index = new_day
        result_obj.period_index = new_period
        result_obj.create_type = "manual"
        await self.db.commit()

        return {
            "success": True,
            "message": "调整成功",
            "has_conflict": False,
            "conflicts": []
        }

    # ============ 事件管理 ============

    async def create_event(self, data: EventCreate) -> SchEvent:
        """创建批量事件"""
        event = SchEvent(
            semester_id=data.semester_id,
            name=data.name,
            event_type=data.event_type.value,
            start_date=data.start_date,
            end_date=data.end_date,
            scope=data.scope,
            target_grade_id=data.target_grade_id,
            target_class_id=data.target_class_id,
            affect_schedule=data.affect_schedule,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def get_events(
        self,
        semester_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[SchEvent]:
        """获取事件列表"""
        query = select(SchEvent).where(SchEvent.semester_id == semester_id)
        if start_date:
            query = query.where(SchEvent.end_date >= start_date)
        if end_date:
            query = query.where(SchEvent.start_date <= end_date)
        query = query.order_by(SchEvent.start_date)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def check_date_affected(self, natural_date: date, class_id: UUID) -> Tuple[bool, Optional[str]]:
        """检查指定日期是否受事件影响"""
        result = await self.db.execute(
            select(SchEvent).where(
                and_(
                    SchEvent.start_date <= natural_date,
                    SchEvent.end_date >= natural_date,
                    SchEvent.status == "active",
                    SchEvent.affect_schedule == True,
                    or_(
                        SchEvent.scope == "all",
                        SchEvent.target_class_id == class_id
                    )
                )
            )
        )
        event = result.scalar_one_or_none()
        if event:
            return True, event.name
        return False, None

    # ============ 长期代课管理 ============

    async def create_replace(self, data: ReplaceCreate) -> SchPlanTeacherReplace:
        """创建长期代课"""
        replace = SchPlanTeacherReplace(
            original_teacher_id=data.original_teacher_id,
            replace_teacher_id=data.replace_teacher_id,
            course_id=data.course_id,
            semester_id=data.semester_id,
            start_date=data.start_date,
            end_date=data.end_date,
            reason=data.reason,
        )
        self.db.add(replace)
        await self.db.commit()
        await self.db.refresh(replace)
        return replace

    async def get_replace_teacher(
        self,
        original_teacher_id: UUID,
        course_id: Optional[UUID],
        natural_date: date
    ) -> Optional[UUID]:
        """获取指定日期的替换教师"""
        query = select(SchPlanTeacherReplace).where(
            and_(
                SchPlanTeacherReplace.original_teacher_id == original_teacher_id,
                SchPlanTeacherReplace.start_date <= natural_date,
                SchPlanTeacherReplace.end_date >= natural_date,
                SchPlanTeacherReplace.status == "active"
            )
        )

        if course_id:
            query = query.where(
                or_(
                    SchPlanTeacherReplace.course_id == course_id,
                    SchPlanTeacherReplace.course_id.is_(None)
                )
            )

        result = await self.db.execute(query)
        replace = result.scalar_one_or_none()

        if replace:
            return replace.replace_teacher_id
        return None

    # ============ 约束管理 ============

    async def create_constraint(self, data: ConstraintCreate) -> SchConstraint:
        """创建约束"""
        constraint = SchConstraint(
            semester_id=data.semester_id,
            constraint_type=data.constraint_type.value,
            name=data.name,
            description=data.description,
            target_type=data.target_type,
            target_id=data.target_id,
            day_index=data.day_index,
            period_start=data.period_start,
            period_end=data.period_end,
            priority=data.priority,
        )
        self.db.add(constraint)
        await self.db.commit()
        await self.db.refresh(constraint)
        return constraint

    async def get_constraints(
        self,
        semester_id: Optional[str] = None,
        constraint_type: Optional[str] = None
    ) -> List[SchConstraint]:
        """获取约束列表"""
        query = select(SchConstraint).where(SchConstraint.is_active == True)
        if semester_id:
            query = query.where(SchConstraint.semester_id == semester_id)
        if constraint_type:
            query = query.where(SchConstraint.constraint_type == constraint_type)
        result = await self.db.execute(query)
        return list(result.scalars().all())
