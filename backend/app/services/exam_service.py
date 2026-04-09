"""
考试服务
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exam import ExamPaper, Question, PaperQuestion
from app.core.exceptions import NotFoundException
from app.services.base_service import BaseService


class PaperService(BaseService[ExamPaper]):
    """试卷服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(ExamPaper, db)

    async def create_paper(self, data: dict, creator_id: UUID) -> ExamPaper:
        data["creator_id"] = creator_id
        return await self.create(data)

    async def add_question_to_paper(
        self, paper_id: UUID, question_id: UUID, order_num: int, score: float
    ) -> PaperQuestion:
        pq = PaperQuestion(
            paper_id=paper_id, question_id=question_id, order_num=order_num, score=score
        )
        self.db.add(pq)
        await self.db.commit()
        return pq

    async def get_paper_questions(self, paper_id: UUID) -> List[Question]:
        result = await self.db.execute(
            select(Question)
            .join(PaperQuestion)
            .where(PaperQuestion.paper_id == paper_id)
        )
        return list(result.scalars().all())


class QuestionService(BaseService[Question]):
    """题目服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(Question, db)

    async def create_question(self, data: dict, creator_id: UUID) -> Question:
        data["creator_id"] = creator_id
        return await self.create(data)

    async def search_questions(
        self,
        keyword: Optional[str] = None,
        question_type: Optional[str] = None,
        difficulty: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        filters = []
        if keyword:
            filters.append(Question.content.ilike(f"%{keyword}%"))
        if question_type:
            filters.append(Question.question_type == question_type)
        if difficulty:
            filters.append(Question.difficulty == difficulty)

        return await self.paginate(page, page_size, filters, "created_at", True)
