"""
教师助手接口 - 教案生成、课件推荐、AI出题
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.lesson_plan import LessonPlan
from app.models.recommendation import Recommendation
from app.schemas.response import success, page_response
from app.schemas.ai import QuestionGenerateRequest, QuestionOutput, QuestionSetOutput
from app.services.ai_service import AIService

router = APIRouter()


# ==================== 教案管理 ====================

class LessonPlanCreate(BaseModel):
    course_id: Optional[UUID] = None
    course_name: Optional[str] = None
    grade_level: Optional[str] = None
    title: str
    teaching_objectives: Optional[str] = None
    teaching_keypoints: Optional[str] = None
    teaching_methods: Optional[str] = None
    teaching_steps: Optional[str] = None
    homework: Optional[str] = None
    ai_generated: bool = False
    source_content: Optional[str] = None


class LessonPlanUpdate(BaseModel):
    course_id: Optional[UUID] = None
    course_name: Optional[str] = None
    grade_level: Optional[str] = None
    title: Optional[str] = None
    teaching_objectives: Optional[str] = None
    teaching_keypoints: Optional[str] = None
    teaching_methods: Optional[str] = None
    teaching_steps: Optional[str] = None
    homework: Optional[str] = None
    status: Optional[str] = None


@router.get("/lesson-plans", response_model=dict)
async def get_lesson_plans(
    keyword: Optional[str] = Query(None),
    grade_level: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教案列表"""
    query = select(LessonPlan).order_by(desc(LessonPlan.created_at))
    
    if keyword:
        query = query.where(LessonPlan.title.ilike(f"%{keyword}%"))
    if grade_level:
        query = query.where(LessonPlan.grade_level == grade_level)
    
    total_result = await db.execute(query)
    total = len(total_result.scalars().all())
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    plans = result.scalars().all()
    
    items = [
        {
            "id": str(p.id),
            "course_id": str(p.course_id) if p.course_id else None,
            "course_name": p.course_name,
            "grade_level": p.grade_level,
            "title": p.title,
            "teaching_objectives": p.teaching_objectives,
            "teaching_keypoints": p.teaching_keypoints,
            "teaching_methods": p.teaching_methods,
            "ai_generated": p.ai_generated,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in plans
    ]
    
    return page_response(items, total, page, page_size)


@router.get("/lesson-plans/{plan_id}", response_model=dict)
async def get_lesson_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教案详情"""
    result = await db.execute(
        select(LessonPlan).where(LessonPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        return success(None)
    
    return success({
        "id": str(plan.id),
        "course_id": str(plan.course_id) if plan.course_id else None,
        "course_name": plan.course_name,
        "grade_level": plan.grade_level,
        "title": plan.title,
        "teaching_objectives": plan.teaching_objectives,
        "teaching_keypoints": plan.teaching_keypoints,
        "teaching_methods": plan.teaching_methods,
        "teaching_steps": plan.teaching_steps,
        "homework": plan.homework,
        "ai_generated": plan.ai_generated,
        "source_content": plan.source_content,
        "status": plan.status,
        "created_by": str(plan.created_by) if plan.created_by else None,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
    })


@router.post("/lesson-plans", response_model=dict)
async def create_lesson_plan(
    data: LessonPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建教案"""
    plan = LessonPlan(**data.model_dump(), created_by=current_user.id)
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return success({"id": str(plan.id)}, "教案创建成功")


@router.put("/lesson-plans/{plan_id}", response_model=dict)
async def update_lesson_plan(
    plan_id: UUID,
    data: LessonPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新教案"""
    result = await db.execute(
        select(LessonPlan).where(LessonPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        return success(message="教案不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)
    
    await db.commit()
    await db.refresh(plan)
    return success({"id": str(plan.id)}, "教案更新成功")


@router.delete("/lesson-plans/{plan_id}", response_model=dict)
async def delete_lesson_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除教案"""
    result = await db.execute(
        select(LessonPlan).where(LessonPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    
    if plan:
        await db.delete(plan)
        await db.commit()
    
    return success(message="教案删除成功")


# ==================== AI教案生成 ====================

class LessonPlanGenerateRequest(BaseModel):
    course_name: str  # 课程名称
    grade_level: str  # 年级
    topic: str  # 课题
    duration: int = 45  # 时长（分钟）
    requirements: Optional[str] = None  # 特殊要求


@router.post("/lesson-plans/generate", response_model=dict)
async def generate_lesson_plan(
    request: LessonPlanGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI生成教案
    注意：需要配置AI服务API密钥才能使用
    """
    ai_service = AIService(db)
    
    # 构建生成提示
    prompt = f"""
请为以下课程生成一份详细的教学教案：

- 课程名称：{request.course_name}
- 年级：{request.grade_level}
- 课题：{request.topic}
- 时长：{request.duration}分钟
{f'- 特殊要求：{request.requirements}' if request.requirements else ''}

请生成包含以下内容的教案：
1. 教学目标
2. 教学重难点
3. 教学方法
4. 教学过程（导入、新课讲授、巩固练习、课堂小结）
5. 作业布置

请以JSON格式返回，格式如下：
{{
    "title": "教案标题",
    "teaching_objectives": "教学目标内容",
    "teaching_keypoints": "教学重难点内容",
    "teaching_methods": "教学方法",
    "teaching_steps": "详细教学过程",
    "homework": "作业布置"
}}
"""
    
    try:
        result = await ai_service.chat(
            current_user.id,
            prompt,
            None,
            "deepseek"
        )
        
        # 保存生成的教案
        plan = LessonPlan(
            course_name=request.course_name,
            grade_level=request.grade_level,
            title=request.topic,
            teaching_objectives=result.get("teaching_objectives"),
            teaching_keypoints=result.get("teaching_keypoints"),
            teaching_methods=result.get("teaching_methods"),
            teaching_steps=result.get("teaching_steps"),
            homework=result.get("homework"),
            ai_generated=True,
            source_content=result.get("raw_response", ""),
            created_by=current_user.id,
            status="draft"
        )
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        
        return success({
            "id": str(plan.id),
            "plan": result
        }, "教案生成成功")
        
    except Exception as e:
        # AI服务不可用时返回示例教案
        sample_plan = {
            "title": f"{request.course_name} - {request.topic}",
            "teaching_objectives": f"1. 知识与技能：掌握{request.topic}的基本概念\n2. 过程与方法：通过案例分析培养学生的思维能力\n3. 情感态度与价值观：激发学生的学习兴趣",
            "teaching_keypoints": f"重点：{request.topic}的核心概念\n难点：如何将理论知识应用到实践中",
            "teaching_methods": "讲授法、讨论法、案例分析法",
            "teaching_steps": f"【导入】({request.duration//6}分钟) 复习相关知识，引出新课题\n【新授】({request.duration//2}分钟) 讲解核心概念和原理\n【练习】({request.duration//6}分钟) 课堂练习\n【小结】({request.duration//6}分钟) 总结本节内容",
            "homework": "完成课后习题，复习本节重点"
        }
        
        plan = LessonPlan(
            course_name=request.course_name,
            grade_level=request.grade_level,
            title=request.topic,
            **sample_plan,
            ai_generated=True,
            source_content="AI服务不可用，使用示例数据",
            created_by=current_user.id,
            status="draft"
        )
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        
        return success({
            "id": str(plan.id),
            "plan": sample_plan,
            "note": "AI服务未配置，使用示例教案"
        }, "教案生成成功")


# ==================== 课件推荐 ====================

@router.get("/courseware/recommend", response_model=dict)
async def recommend_courseware(
    course_name: str = Query(..., description="课程名称"),
    topic: Optional[str] = Query(None, description="具体课题"),
    grade_level: Optional[str] = Query(None, description="年级"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取课件推荐
    注意：需要配置AI服务API密钥才能使用
    """
    ai_service = AIService(db)
    
    prompt = f"""
请为以下课程推荐合适的课件和教学资源：

- 课程名称：{course_name}
{f'- 具体课题：{topic}' if topic else ''}
{f'- 年级：{grade_level}' if grade_level else ''}

请推荐3-5个合适的课件资源，包括：
1. 课件名称
2. 课件类型（PPT/视频/动画等）
3. 适用场景
4. 简要说明

请以JSON数组格式返回：
[
    {{
        "name": "课件名称",
        "type": "课件类型",
        "scenario": "适用场景",
        "description": "简要说明"
    }}
]
"""
    
    try:
        result = await ai_service.chat(
            current_user.id,
            prompt,
            None,
            "deepseek"
        )
        return success(result)
    except Exception:
        # AI服务不可用时返回示例推荐
        sample_recommendations = [
            {
                "name": f"{course_name}基础知识课件",
                "type": "PPT",
                "scenario": "新授课",
                "description": "包含基础概念讲解和图文说明"
            },
            {
                "name": f"{course_name}案例分析",
                "type": "PPT",
                "scenario": "习题课",
                "description": "典型例题分析和解答"
            },
            {
                "name": f"{course_name}微课视频",
                "type": "视频",
                "scenario": "翻转课堂",
                "description": "5-10分钟的知识点讲解视频"
            }
        ]
        return success({
            "recommendations": sample_recommendations,
            "note": "AI服务未配置，使用示例推荐"
        })


# ==================== AI 出题系统 ====================

@router.post("/questions/generate", response_model=dict)
async def generate_questions(
    request: QuestionGenerateRequest,
    current_user: User = Depends(get_current_user),
):
    """
    AI 出题：生成练习题/试卷题目

    支持题型：
    - single: 单选题
    - multiple: 多选题
    - fill: 填空题
    - essay: 解答题
    - calculation: 计算题
    """
    ai_service = AIService(db=None)  # 出题不需要 db

    try:
        result = await ai_service.generate_questions(request)
        return success({
            "set_id": result.set_id,
            "title": result.title,
            "course_name": result.course_name,
            "grade_level": result.grade_level,
            "topic": result.topic,
            "total_count": result.total_count,
            "questions": [
                {
                    "content": q.content,
                    "question_type": q.question_type,
                    "options": [{"label": o.label, "content": o.content, "is_correct": o.is_correct} for o in q.options] if q.options else None,
                    "answer": q.answer,
                    "analysis": q.analysis,
                    "difficulty": q.difficulty,
                    "score": q.score,
                    "knowledge_points": q.knowledge_points,
                    "source": q.source,
                    "saved": q.saved,
                }
                for q in result.questions
            ],
            "generated_at": result.generated_at,
            "saved_count": result.saved_count,
        }, "题目生成成功")
    except Exception as e:
        return success({
            "set_id": "",
            "title": f"{request.course_name} - {request.topic} 练习题",
            "total_count": 0,
            "questions": [],
            "generated_at": datetime.now().isoformat(),
            "error": str(e),
        }, "题目生成失败")


class SaveQuestionRequest(BaseModel):
    """保存题目请求"""
    content: str
    question_type: str = "single"
    options: Optional[List[dict]] = None
    answer: Optional[str] = None
    analysis: Optional[str] = None
    difficulty: int = 2
    score: float = 5.0
    knowledge_points: List[str] = []


@router.post("/questions/save", response_model=dict)
async def save_question(
    request: SaveQuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    保存生成的题目到题库

    保存后可添加到试卷或用于练习。
    """
    from app.schemas.ai import QuestionOption
    from app.services.ai_service import AIService

    # 转换 options
    options = None
    if request.options:
        options = [
            QuestionOption(
                label=opt.get("label", chr(65 + i)),
                content=opt.get("content", ""),
                is_correct=opt.get("is_correct", False),
            )
            for i, opt in enumerate(request.options)
        ]

    question_output = QuestionOutput(
        content=request.content,
        question_type=request.question_type,
        options=options,
        answer=request.answer,
        analysis=request.analysis,
        difficulty=request.difficulty,
        score=request.score,
        knowledge_points=request.knowledge_points,
        source="ai",
        saved=True,
    )

    ai_service = AIService(db)
    question_id = await ai_service.save_generated_question(question_output, current_user.id)

    return success({
        "question_id": question_id,
    }, "题目保存成功")


@router.post("/questions/save-batch", response_model=dict)
async def save_questions_batch(
    questions: List[SaveQuestionRequest],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    批量保存生成的题目到题库
    """
    from app.schemas.ai import QuestionOption
    from app.services.ai_service import AIService

    ai_service = AIService(db)
    saved_ids = []

    for q_req in questions:
        options = None
        if q_req.options:
            options = [
                QuestionOption(
                    label=opt.get("label", chr(65 + i)),
                    content=opt.get("content", ""),
                    is_correct=opt.get("is_correct", False),
                )
                for i, opt in enumerate(q_req.options)
            ]

        question_output = QuestionOutput(
            content=q_req.content,
            question_type=q_req.question_type,
            options=options,
            answer=q_req.answer,
            analysis=q_req.analysis,
            difficulty=q_req.difficulty,
            score=q_req.score,
            knowledge_points=q_req.knowledge_points,
            source="ai",
            saved=True,
        )

        question_id = await ai_service.save_generated_question(question_output, current_user.id)
        saved_ids.append(question_id)

    return success({
        "saved_count": len(saved_ids),
        "question_ids": saved_ids,
    }, f"成功保存 {len(saved_ids)} 道题目")
