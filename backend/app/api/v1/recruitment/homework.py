from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.homework import Homework, HomeworkSubmission, WrongQuestion, HomeworkFeedback
from app.models.notification import Notification
from app.schemas.homework import (
    HomeworkCreate, HomeworkUpdate,
    HomeworkSubmissionCreate, HomeworkSubmissionUpdate,
    WrongQuestionCreate, HomeworkFeedbackCreate
)
from app.schemas.response import success, page_response

router = APIRouter()


def to_naive_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    """将带时区的 datetime 转换为不带时区的 datetime"""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


@router.get("/homeworks", response_model=dict)
async def get_homeworks(
    course_id: Optional[str] = Query(None),
    class_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Homework).order_by(Homework.created_at.desc())
    
    if course_id:
        query = query.where(Homework.course_id == UUID(course_id))
    if class_id:
        query = query.where(Homework.class_id == UUID(class_id))
    if status:
        query = query.where(Homework.status == status)
    
    result = await db.execute(query)
    homeworks = result.scalars().all()
    
    total = len(homeworks)
    offset = (page - 1) * page_size
    items = homeworks[offset:offset + page_size]
    
    return page_response([
        {
            "id": str(h.id),
            "title": h.title,
            "content": h.content,
            "homework_type": h.homework_type,
            "total_score": float(h.total_score) if h.total_score else 100,
            "status": h.status,
            "created_at": h.created_at.isoformat(),
        }
        for h in items
    ], total, page, page_size)


@router.post("/homeworks", response_model=dict)
async def create_homework(
    data: HomeworkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    homework = Homework(
        title=data.title,
        content=data.content,
        course_id=UUID(data.course_id) if data.course_id else None,
        teacher_id=current_user.id,
        grade_id=UUID(data.grade_id) if data.grade_id else None,
        class_ids=data.class_ids if data.class_ids else None,
        homework_type=data.homework_type,
        total_score=data.total_score,
        submit_start=to_naive_datetime(data.submit_start),
        submit_end=to_naive_datetime(data.submit_end),
        notify_enabled=data.notify_enabled,
        status="draft",
    )
    db.add(homework)
    await db.commit()
    await db.refresh(homework)
    return success({"id": str(homework.id)}, "作业创建成功")


@router.put("/homeworks/{homework_id}", response_model=dict)
async def update_homework(
    homework_id: UUID,
    data: HomeworkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Homework).where(Homework.id == homework_id))
    homework = result.scalar_one_or_none()
    
    if not homework:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("作业不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    if 'submit_start' in update_data:
        update_data['submit_start'] = to_naive_datetime(update_data['submit_start'])
    if 'submit_end' in update_data:
        update_data['submit_end'] = to_naive_datetime(update_data['submit_end'])
    for key, value in update_data.items():
        setattr(homework, key, value)
    
    await db.commit()
    return success({"id": str(homework.id)}, "作业更新成功")


@router.get("/homeworks/{homework_id}/submissions", response_model=dict)
async def get_submissions(
    homework_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(HomeworkSubmission)
        .where(HomeworkSubmission.homework_id == homework_id)
        .order_by(HomeworkSubmission.submitted_at.desc())
    )
    submissions = result.scalars().all()
    
    return success([
        {
            "id": str(s.id),
            "student_id": str(s.student_id),
            "content": s.content,
            "score": float(s.score) if s.score else None,
            "status": s.status,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
        }
        for s in submissions
    ])


@router.post("/homeworks/{homework_id}/submit", response_model=dict)
async def submit_homework(
    homework_id: UUID,
    data: HomeworkSubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = HomeworkSubmission(
        homework_id=homework_id,
        student_id=current_user.id,
        content=data.content,
        attachment_urls=data.attachment_urls,
        status="submitted",
        submitted_at=datetime.now(),
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return success({"id": str(submission.id)}, "提交成功")


@router.put("/submissions/{submission_id}/grade", response_model=dict)
async def grade_submission(
    submission_id: UUID,
    score: float,
    feedback: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(HomeworkSubmission).where(HomeworkSubmission.id == submission_id))
    submission = result.scalar_one_or_none()
    
    if not submission:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("提交记录不存在")
    
    submission.score = score
    submission.feedback = feedback
    submission.graded_at = datetime.now()
    
    await db.commit()
    return success(message="评分成功")


@router.get("/wrong-questions", response_model=dict)
async def get_wrong_questions(
    student_id: Optional[str] = Query(None),
    is_mastered: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(WrongQuestion).order_by(WrongQuestion.created_at.desc())
    
    if student_id:
        query = query.where(WrongQuestion.student_id == UUID(student_id))
    if is_mastered is not None:
        query = query.where(WrongQuestion.is_mastered == is_mastered)
    
    result = await db.execute(query)
    questions = result.scalars().all()
    
    total = len(questions)
    offset = (page - 1) * page_size
    items = questions[offset:offset + page_size]
    
    return page_response([
        {
            "id": str(q.id),
            "question_content": q.question_content,
            "question_type": q.question_type,
            "is_reviewed": q.is_reviewed,
            "is_mastered": q.is_mastered,
            "review_count": q.review_count,
            "created_at": q.created_at.isoformat(),
        }
        for q in items
    ], total, page, page_size)


@router.post("/wrong-questions", response_model=dict)
async def create_wrong_question(
    data: WrongQuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = WrongQuestion(
        student_id=current_user.id,
        question_content=data.question_content,
        question_type=data.question_type,
        correct_answer=data.correct_answer,
        student_answer=data.student_answer,
        score=data.score,
        source_type=data.source_type,
        source_id=data.source_id,
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return success({"id": str(question.id)}, "错题添加成功")


@router.get("/homeworks/{homework_id}/feedbacks", response_model=dict)
async def get_homework_feedbacks(
    homework_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(HomeworkFeedback)
        .where(HomeworkFeedback.homework_id == homework_id)
        .order_by(HomeworkFeedback.created_at.desc())
    )
    feedbacks = result.scalars().all()
    
    return success([
        {
            "id": str(f.id),
            "feedback_type": f.feedback_type,
            "content": f.content,
            "is_resolved": f.is_resolved,
            "created_at": f.created_at.isoformat(),
        }
        for f in feedbacks
    ])


@router.post("/homeworks/{homework_id}/feedback", response_model=dict)
async def create_feedback(
    homework_id: UUID,
    data: HomeworkFeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    feedback = HomeworkFeedback(
        homework_id=homework_id,
        student_id=current_user.id,
        parent_id=current_user.id,
        feedback_type=data.feedback_type,
        content=data.content,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return success({"id": str(feedback.id)}, "反馈提交成功")


@router.get("/homeworks/stats", response_model=dict)
async def get_homework_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.homework import Homework, HomeworkSubmission, WrongQuestion
    
    draft_result = await db.execute(
        select(func.count()).select_from(Homework).where(Homework.status == "draft")
    )
    published_result = await db.execute(
        select(func.count()).select_from(Homework).where(Homework.status == "published")
    )
    submitted_result = await db.execute(
        select(func.count()).select_from(HomeworkSubmission)
    )
    wrong_result = await db.execute(
        select(func.count()).select_from(WrongQuestion).where(WrongQuestion.is_mastered == False)
    )
    
    return success({
        "draft": draft_result.scalar(),
        "published": published_result.scalar(),
        "submitted": submitted_result.scalar(),
        "wrong_questions": wrong_result.scalar(),
    })