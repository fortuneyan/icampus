"""
仪表盘服务
"""

from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.student import Student
from app.models.class_model import Class
from app.models.course import Course
from app.models.resource import Resource
from app.models.attendance import AttendanceRecord


class DashboardService:
    """仪表盘服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self) -> dict:
        """获取数据概览"""
        student_count = await self.db.execute(select(func.count()).select_from(Student))
        teacher_count = await self.db.execute(
            select(func.count()).select_from(User).where(User.status == "active")
        )
        class_count = await self.db.execute(select(func.count()).select_from(Class))
        course_count = await self.db.execute(select(func.count()).select_from(Course))
        resource_count = await self.db.execute(
            select(func.count())
            .select_from(Resource)
            .where(Resource.status == "published")
        )

        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        attendance_result = await self.db.execute(
            select(func.count())
            .select_from(AttendanceRecord)
            .where(AttendanceRecord.created_at >= today_start)
        )
        total_attendance = attendance_result.scalar() or 0
        normal_result = await self.db.execute(
            select(func.count())
            .select_from(AttendanceRecord)
            .where(
                AttendanceRecord.created_at >= today_start,
                AttendanceRecord.status == "normal",
            )
        )
        normal_count = normal_result.scalar() or 0
        attendance_rate = (
            round(normal_count / total_attendance * 100, 2)
            if total_attendance > 0
            else 0
        )

        return {
            "student_count": student_count.scalar() or 0,
            "teacher_count": teacher_count.scalar() or 0,
            "class_count": class_count.scalar() or 0,
            "course_count": course_count.scalar() or 0,
            "resource_count": resource_count.scalar() or 0,
            "today_attendance_rate": attendance_rate,
        }

    async def get_statistics(self) -> dict:
        """获取统计分析"""
        return {
            "student_trend": [
                {"month": "1月", "value": 1000},
                {"month": "2月", "value": 1100},
                {"month": "3月", "value": 1200},
            ],
            "score_trend": [
                {"subject": "语文", "avg": 85},
                {"subject": "数学", "avg": 88},
                {"subject": "英语", "avg": 82},
            ],
            "resource_usage": [
                {"type": "视频", "count": 500},
                {"type": "文档", "count": 300},
                {"type": "图片", "count": 200},
            ],
        }

    async def get_charts(self) -> dict:
        """获取图表数据"""
        return {
            "student_gender": {
                "labels": ["男", "女"],
                "datasets": [{"data": [600, 550]}],
            },
            "resource_type": {
                "labels": ["视频", "文档", "图片"],
                "datasets": [{"data": [40, 35, 25]}],
            },
            "attendance_trend": {
                "labels": ["周一", "周二", "周三", "周四", "周五"],
                "datasets": [{"data": [95, 92, 94, 91, 93]}],
            },
        }

    async def get_quick_actions(self, user_id: UUID) -> List[dict]:
        """获取快捷操作"""
        return [
            {
                "id": "1",
                "name": "添加学生",
                "icon": "UserPlus",
                "path": "/edu/students",
                "permission": "edu:student:create",
            },
            {
                "id": "2",
                "name": "成绩录入",
                "icon": "EditPen",
                "path": "/edu/scores",
                "permission": "edu:score:create",
            },
            {
                "id": "3",
                "name": "发布通知",
                "icon": "Bell",
                "path": "/notice/notices",
                "permission": "notice:notice:create",
            },
            {
                "id": "4",
                "name": "资源上传",
                "icon": "Upload",
                "path": "/resource/resources",
                "permission": "resource:resource:create",
            },
        ]
