"""
成绩服务
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.score import Score
from app.core.exceptions import NotFoundException, ConflictException
from app.services.base_service import BaseService


class ScoreService(BaseService[Score]):
    """成绩服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(Score, db)

    async def get_student_course_score(
        self, student_id: UUID, course_id: UUID, semester: str
    ) -> Optional[Score]:
        """获取学生某课程成绩"""
        return await self.get_by_field("student_id", student_id)

    async def create_score(self, data: dict) -> Score:
        """创建成绩"""
        return await self.create(data)

    async def update_score(self, score_id: UUID, data: dict) -> Score:
        """更新成绩"""
        score = await self.get(score_id)
        if not score:
            raise NotFoundException("成绩不存在")

        return await self.update(score_id, data)

    async def batch_create_scores(self, scores_data: List[dict]) -> List[Score]:
        """批量创建成绩"""
        scores = []
        for data in scores_data:
            score = await self.create(data)
            scores.append(score)
        return scores

    async def get_score_statistics(self, course_id: UUID, semester: str) -> dict:
        """获取成绩统计"""
        filters = [Score.course_id == course_id]
        if semester:
            filters.append(Score.semester == semester)

        scores = await self.get_all(filters)

        if not scores:
            return {
                "total": 0,
                "avg_score": 0,
                "max_score": 0,
                "min_score": 0,
                "pass_rate": 0,
            }

        score_values = [s.score for s in scores if s.score is not None]
        if not score_values:
            return {
                "total": 0,
                "avg_score": 0,
                "max_score": 0,
                "min_score": 0,
                "pass_rate": 0,
            }

        passed = len([s for s in score_values if s >= 60])

        return {
            "total": len(score_values),
            "avg_score": round(sum(score_values) / len(score_values), 2),
            "max_score": max(score_values),
            "min_score": min(score_values),
            "pass_rate": round(passed / len(score_values) * 100, 2),
        }

    async def search_scores(
        self,
        student_id: Optional[UUID] = None,
        course_id: Optional[UUID] = None,
        semester: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """搜索成绩"""
        filters = []

        if student_id:
            filters.append(Score.student_id == student_id)
        if course_id:
            filters.append(Score.course_id == course_id)
        if semester:
            filters.append(Score.semester == semester)

        return await self.paginate(page, page_size, filters, "recorded_at", True)
