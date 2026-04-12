from fastapi import APIRouter
from app.api.v1.exam import exams, question_bank, quality_score, papers, reports

router = APIRouter()
router.include_router(exams.router, prefix="", tags=["考试管理"])
router.include_router(question_bank.router, prefix="", tags=["题库管理"])
router.include_router(quality_score.router, prefix="", tags=["题库质量评分"])
router.include_router(papers.router, prefix="", tags=["智能组卷"])
router.include_router(reports.router, prefix="", tags=["成绩报表"])
