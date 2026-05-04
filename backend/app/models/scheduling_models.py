"""
智能排课模块 - 数据库模型

实现设计文档要求的5张核心表：
1. sch_cycle (周次组合底表)
2. sch_calendar_map (日历映射表)
3. sch_plan (课程规划表)
4. sch_result (核心排课结果表)
5. sch_patch (调课图层表)
"""

from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import (
    Column, String, Integer, DateTime, Date, Boolean,
    ForeignKey, Text, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SchCycle(Base):
    """
    周次组合底表 - 破除"自然周"的毒咒

    设计初衷：不要用"第1周、第2周"去关联课表，
    因为节假日会把自然周切碎。用"周次组合ID"作为课表的最小分发单元。
    """
    __tablename__ = "sch_cycle"

    id = Column(String(32), primary_key=True)  # 如 "W01_03"
    semester_id = Column(String(32), ForeignKey("sch_semester.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, default=False)
    cycle_type = Column(String(20), default="regular")  # regular, exam, holiday
    remark = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    semester = relationship("SchSemester", back_populates="cycles")
    calendar_maps = relationship("SchCalendarMap", back_populates="cycle")
    plans = relationship("SchPlan", back_populates="cycle")
    results = relationship("SchResult", back_populates="cycle")


class SchSemester(Base):
    """
    学期表 - 管理学年学期信息
    """
    __tablename__ = "sch_semester"

    id = Column(String(32), primary_key=True)  # 如 "2024_FALL"
    name = Column(String(50), nullable=False)  # 如 "2024年秋季学期"
    academic_year = Column(String(9), nullable=False)  # 如 "2024-2025"
    semester = Column(Integer, nullable=False)  # 1=上学期, 2=下学期
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), default="active")  # active, archived
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    cycles = relationship("SchCycle", back_populates="semester")
    templates = relationship("SchTemplate", back_populates="semester")


class SchCalendarMap(Base):
    """
    日历映射表 - 节假日调休的终极解法

    设计初衷：解决"周六上周一课"这种中国式调休。
    不修改课表，只修改"日历指向"。
    """
    __tablename__ = "sch_calendar_map"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    natural_date = Column(Date, nullable=False, unique=True)  # 真实的自然日
    cycle_id = Column(String(32), ForeignKey("sch_cycle.id"), nullable=False)
    exec_day = Column(Integer, nullable=False)  # 核心！这天要执行"星期几"的课表 (1-7)
    is_workday = Column(Boolean, default=True)  # 是否工作日
    is_holiday = Column(Boolean, default=False)  # 是否放假（覆盖上面的exec_day）
    remark = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    cycle = relationship("SchCycle", back_populates="calendar_maps")

    # 索引
    __table_args__ = (
        Index("idx_calendar_natural_date", "natural_date"),
        Index("idx_calendar_cycle_exec_day", "cycle_id", "exec_day"),
    )


class SchTemplate(Base):
    """
    课表模板表 - 支持多套课表模板并存

    设计初衷：支持考试周、入学教育周等特殊时期的课表模板
    """
    __tablename__ = "sch_template"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    semester_id = Column(String(32), ForeignKey("sch_semester.id"), nullable=False)
    name = Column(String(50), nullable=False)  # 如 "期中考试模板"、"常规模板"
    template_type = Column(String(20), default="regular")  # regular, exam, orientation, custom
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    priority = Column(Integer, default=0)  # 优先级，数值越大优先级越高
    is_active = Column(Boolean, default=True)
    remark = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    semester = relationship("SchSemester", back_populates="templates")
    periods = relationship("SchPeriod", back_populates="template")

    __table_args__ = (
        UniqueConstraint("semester_id", "name", name="uq_template_semester_name"),
    )


class SchPeriod(Base):
    """
    节次表 - 定义每天的课程节次
    """
    __tablename__ = "sch_period"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("sch_template.id"), nullable=False)
    period_index = Column(Integer, nullable=False)  # 第几节 (1-10)
    start_time = Column(String(5), nullable=False)  # 如 "08:00"
    end_time = Column(String(5), nullable=False)  # 如 "08:45"
    period_type = Column(String(20), default="normal")  # morning, afternoon, evening, break, self_study
    duration = Column(Integer, default=45)  # 时长（分钟）
    remark = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # 关联
    template = relationship("SchTemplate", back_populates="periods")

    __table_args__ = (
        UniqueConstraint("template_id", "period_index", name="uq_period_template_index"),
    )


class SchPlan(Base):
    """
    课程规划表 - 算法启动前的输入清单

    设计初衷：告诉系统，在这个周次组合里，
    每个班总共要上多少节什么课，由谁来上。这是排课的"原材料"。
    """
    __tablename__ = "sch_plan"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    cycle_id = Column(String(32), ForeignKey("sch_cycle.id"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    total_hours = Column(Integer, nullable=False)  # 总课时数
    is_continuous = Column(Boolean, default=False)  # 是否需要连排
    continuous_length = Column(Integer, default=1)  # 连排几节
    priority = Column(Integer, default=0)  # 优先级
    remark = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    cycle = relationship("SchCycle", back_populates="plans")
    results = relationship(
        "SchResult",
        primaryjoin=(
            "and_("
            "SchPlan.cycle_id == SchResult.cycle_id, "
            "SchPlan.class_id == SchResult.class_id, "
            "SchPlan.teacher_id == SchResult.teacher_id, "
            "SchPlan.course_id == SchResult.course_id"
            ")"
        ),
        foreign_keys="[SchResult.cycle_id, SchResult.class_id, SchResult.teacher_id, SchResult.course_id]",
        viewonly=True,
        lazy="select",
    )

    # 索引
    __table_args__ = (
        Index("idx_plan_cycle_class", "cycle_id", "class_id"),
        Index("idx_plan_cycle_teacher", "cycle_id", "teacher_id"),
    )


class SchResult(Base):
    """
    核心排课结果表 - 人工"钉钉子"与机器"填空"的战场

    设计初衷：这是最核心的表。必须能区分哪些是人工排的死规定，
    哪些是机器塞进去的。
    """
    __tablename__ = "sch_result"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    cycle_id = Column(String(32), ForeignKey("sch_cycle.id"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id"), nullable=True)
    day_index = Column(Integer, nullable=False)  # 星期几 (1-7)
    period_index = Column(Integer, nullable=False)  # 第几节 (1-10)
    week_start = Column(Integer, nullable=True)  # 周次范围开始
    week_end = Column(Integer, nullable=True)  # 周次范围结束
    is_locked = Column(Boolean, default=False)  # 核心！是否被人工锁定
    create_type = Column(String(20), default="auto")  # manual, auto_fill, ai_optimize
    template_id = Column(UUID(as_uuid=True), ForeignKey("sch_template.id"), nullable=True)  # 所属模板
    remark = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    cycle = relationship("SchCycle", back_populates="results")
    plan = relationship(
        "SchPlan",
        primaryjoin=(
            "and_("
            "SchResult.cycle_id == SchPlan.cycle_id, "
            "SchResult.class_id == SchPlan.class_id, "
            "SchResult.teacher_id == SchPlan.teacher_id, "
            "SchResult.course_id == SchPlan.course_id"
            ")"
        ),
        foreign_keys="[SchResult.cycle_id, SchResult.class_id, SchResult.teacher_id, SchResult.course_id]",
        viewonly=True,
        lazy="select",
    )

    # 唯一约束：同一cycle同一时间同一班级/教师只能有一条记录
    __table_args__ = (
        UniqueConstraint(
            "cycle_id", "day_index", "period_index", "class_id",
            name="uq_result_time_class"
        ),
        UniqueConstraint(
            "cycle_id", "day_index", "period_index", "teacher_id",
            name="uq_result_time_teacher"
        ),
        Index("idx_result_cycle_day_period", "cycle_id", "day_index", "period_index"),
        Index("idx_result_class", "class_id"),
        Index("idx_result_teacher", "teacher_id"),
    )


class SchPatch(Base):
    """
    调课图层表/补丁表 - 不动底表的乾坤大挪移

    设计初衷：平时张老师生病了要和李老师换课，
    绝对不要去UPDATE sch_result表（那是基准底表）。
    在这里插入一条"补丁"，查询时动态叠加。
    """
    __tablename__ = "sch_patch"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    natural_date = Column(Date, nullable=False)  # 具体哪一天调课
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    day_index = Column(Integer, nullable=False)  # 原星期几 (1-7)
    period_index = Column(Integer, nullable=False)  # 第几节
    original_teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    patch_teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    original_course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=True)
    patch_course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=True)
    original_room_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id"), nullable=True)
    patch_room_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id"), nullable=True)
    patch_type = Column(String(20), default="swap")  # swap, substitute, cancel, self_study
    status = Column(String(20), default="active")  # active, cancelled
    reason = Column(String(200), nullable=True)
    applicant_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    remark = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 索引
    __table_args__ = (
        Index("idx_patch_natural_date", "natural_date"),
        Index("idx_patch_class_date", "class_id", "natural_date"),
        Index("idx_patch_status", "status"),
    )


class SchConstraint(Base):
    """
    排课约束表 - 存储硬约束和软约束规则
    """
    __tablename__ = "sch_constraint"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    semester_id = Column(String(32), ForeignKey("sch_semester.id"), nullable=True)
    constraint_type = Column(String(20), nullable=False)  # HARD, SOFT
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    target_type = Column(String(20), nullable=True)  # teacher, class, course, room
    target_id = Column(UUID(as_uuid=True), nullable=True)
    day_index = Column(Integer, nullable=True)  # 限制星期几
    period_start = Column(Integer, nullable=True)  # 限制起始节次
    period_end = Column(Integer, nullable=True)  # 限制结束节次
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_constraint_semester_type", "semester_id", "constraint_type"),
        Index("idx_constraint_target", "target_type", "target_id"),
    )


class SchEvent(Base):
    """
    批量事件表 - 运动会、春游等全校性事件
    """
    __tablename__ = "sch_event"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    semester_id = Column(String(32), ForeignKey("sch_semester.id"), nullable=False)
    name = Column(String(100), nullable=False)
    event_type = Column(String(50), nullable=False)  # sports_meet, excursion, exam, custom
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    scope = Column(String(20), default="all")  # all, grade, class
    target_grade_id = Column(UUID(as_uuid=True), nullable=True)
    target_class_id = Column(UUID(as_uuid=True), nullable=True)
    affect_schedule = Column(Boolean, default=True)  # 是否影响课表
    status = Column(String(20), default="active")  # active, cancelled, completed
    remark = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_event_semester_date", "semester_id", "start_date", "end_date"),
    )


class SchPlanTeacherReplace(Base):
    """
    长期代课表 - 产假、病假等长期替换教师
    """
    __tablename__ = "sch_plan_teacher_replace"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    original_teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    replace_teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=True)
    semester_id = Column(String(32), ForeignKey("sch_semester.id"), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String(200), nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_replace_teacher", "original_teacher_id", "status"),
        Index("idx_replace_semester", "semester_id"),
    )
