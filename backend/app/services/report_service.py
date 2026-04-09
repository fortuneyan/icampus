"""
报表服务
"""

from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.models.score import Score
from app.models.attendance import AttendanceRecord
from app.models.grade_model import Grade
from app.models.class_model import Class


class ReportService:
    """报表服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_student_report(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> dict:
        """学生统计报表"""
        total_result = await self.db.execute(select(func.count()).select_from(Student))
        total_students = total_result.scalar() or 0

        grade_result = await self.db.execute(
            select(Grade.name, func.count(Student.id))
            .join(Student, Student.grade_id == Grade.id)
            .group_by(Grade.name)
        )
        by_grade = [{"name": r[0], "count": r[1]} for r in grade_result.fetchall()]

        class_result = await self.db.execute(
            select(Class.name, func.count(Student.id))
            .join(Student, Student.class_id == Class.id)
            .group_by(Class.name)
        )
        by_class = [{"name": r[0], "count": r[1]} for r in class_result.fetchall()]

        return {
            "total_students": total_students,
            "by_grade": by_grade,
            "by_class": by_class,
            "enrollment_trend": [
                {"month": "1月", "count": 100},
                {"month": "2月", "count": 120},
            ],
        }

    async def get_score_report(
        self, course_id: Optional[UUID] = None, semester: Optional[str] = None
    ) -> dict:
        """成绩统计报表"""
        filters = [Score.score.isnot(None)]
        if course_id:
            filters.append(Score.course_id == course_id)
        if semester:
            filters.append(Score.semester == semester)

        result = await self.db.execute(select(Score).where(*filters))
        scores = list(result.scalars().all())

        if not scores:
            return {
                "avg_score": 0,
                "pass_rate": 0,
                "score_distribution": [],
                "subject_ranking": [],
            }

        score_values = [float(s.score) for s in scores]
        avg_score = round(sum(score_values) / len(score_values), 2)
        pass_count = len([s for s in score_values if s >= 60])
        pass_rate = round(pass_count / len(score_values) * 100, 2)

        distribution = [
            {"range": "0-60", "count": len([s for s in score_values if s < 60])},
            {"range": "60-70", "count": len([s for s in score_values if 60 <= s < 70])},
            {"range": "70-80", "count": len([s for s in score_values if 70 <= s < 80])},
            {"range": "80-90", "count": len([s for s in score_values if 80 <= s < 90])},
            {"range": "90-100", "count": len([s for s in score_values if s >= 90])},
        ]

        return {
            "avg_score": avg_score,
            "pass_rate": pass_rate,
            "score_distribution": distribution,
            "subject_ranking": [],
        }

    async def get_attendance_report(
        self, start_date: datetime, end_date: datetime, user_id: Optional[UUID] = None
    ) -> dict:
        """考勤统计报表"""
        filters = [
            AttendanceRecord.created_at >= start_date,
            AttendanceRecord.created_at <= end_date,
        ]
        if user_id:
            filters.append(AttendanceRecord.user_id == user_id)

        result = await self.db.execute(select(AttendanceRecord).where(*filters))
        records = list(result.scalars().all())

        total = len(records)
        normal_count = len([r for r in records if r.status == "normal"])
        late_count = len([r for r in records if r.status == "late"])

        attendance_rate = round(normal_count / total * 100, 2) if total > 0 else 0

        return {
            "attendance_rate": attendance_rate,
            "normal_count": normal_count,
            "late_count": late_count,
            "absent_count": total - normal_count - late_count,
            "trend": [],
        }

    async def create_custom_report(
        self,
        user_id: UUID,
        name: str,
        report_type: str,
        config: dict,
        is_public: bool = False,
    ) -> dict:
        """创建自定义报表"""
        from app.models.dashboard import ReportConfig

        report = ReportConfig(
            name=name,
            report_type=report_type,
            config=config,
            creator_id=user_id,
            is_public=is_public,
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return {"id": str(report.id), "name": report.name}
