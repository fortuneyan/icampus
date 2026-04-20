"""
学习诊断与个性化推荐接口
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.score import Score
from app.models.learning_record import LearningRecord
from app.schemas.response import success, page_response
from app.services.ai_service import AIService

router = APIRouter()


# ==================== 学习诊断 ====================


class DiagnosisRequest(BaseModel):
    student_id: UUID
    course_id: Optional[UUID] = None
    course_name: Optional[str] = None
    recent_scores: Optional[List[dict]] = None  # 最近成绩
    learning_records: Optional[List[dict]] = None  # 学习记录


@router.post("/diagnosis", response_model=dict)
async def diagnose_learning(
    request: DiagnosisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI学习诊断
    分析学生的学习情况，提供诊断报告和改进建议
    """
    ai_service = AIService(db)

    # 获取学生的最近成绩
    score_query = (
        select(Score)
        .where(Score.student_id == request.student_id)
        .order_by(desc(Score.created_at))
        .limit(10)
    )
    score_result = await db.execute(score_query)
    scores = score_result.scalars().all()

    scores_data = [
        {
            "course": s.course_id,
            "score": float(s.score) if s.score else 0,
            "exam_type": s.exam_type,
        }
        for s in scores
    ]

    # 获取学生的学习记录
    record_query = (
        select(LearningRecord)
        .where(LearningRecord.user_id == request.student_id)
        .order_by(desc(LearningRecord.created_at))
        .limit(20)
    )
    record_result = await db.execute(record_query)
    records = record_result.scalars().all()

    records_data = [
        {
            "resource_name": r.resource_name,
            "action_type": r.action_type,
            "duration": r.duration,
            "progress": r.progress,
        }
        for r in records
    ]

    # 构建诊断提示
    prompt = f"""
请对学生的学习情况进行诊断分析：

学生ID: {request.student_id}
{f"课程: {request.course_name}" if request.course_name else ""}

最近成绩：
{scores_data}

学习记录：
{records_data}

请提供以下诊断内容：
1. 学习状态总体评价
2. 各维度分析（知识掌握、学习态度、时间管理等）
3. 发现的问题
4. 改进建议

请以JSON格式返回：
{{
    "overall_evaluation": "总体评价",
    "knowledge_mastery": "知识掌握分析",
    "learning_attitude": "学习态度分析",
    "time_management": "时间管理分析",
    "problems": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"],
    "recommended_resources": [
        {{"name": "资源名称", "type": "资源类型", "reason": "推荐原因"}}
    ]
}}
"""

    try:
        result = await ai_service.chat(current_user.id, prompt, None, "deepseek")
        return success(result)
    except Exception:
        # AI服务不可用时返回基础诊断
        avg_score = (
            sum(s.get("score", 0) for s in scores_data) / len(scores_data)
            if scores_data
            else 0
        )

        basic_diagnosis = {
            "overall_evaluation": "基于成绩数据的初步诊断"
            if scores_data
            else "暂无足够数据进行诊断",
            "knowledge_mastery": f"最近{len(scores_data)}次考试平均成绩为{avg_score:.1f}分"
            if scores_data
            else "暂无成绩数据",
            "learning_attitude": "建议保持规律的学习习惯"
            if records_data
            else "暂无学习记录",
            "time_management": "建议合理安排学习时间",
            "problems": ["需要更多练习"] if avg_score < 60 else [],
            "suggestions": [
                "1. 做好课前预习和课后复习",
                "2. 建立错题本，针对性练习",
                "3. 积极参与课堂互动",
                "4. 定期回顾已学知识",
            ],
            "recommended_resources": [
                {"name": "基础知识讲解", "type": "文档", "reason": "巩固基础"},
                {"name": "练习题库", "type": "题库", "reason": "提升解题能力"},
            ],
            "note": "AI服务未配置，使用基础诊断",
        }
        return success(basic_diagnosis)


@router.get("/diagnosis/student/{student_id}", response_model=dict)
async def get_student_diagnosis(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学生的学习诊断历史"""
    # 获取学生的成绩统计
    score_query = (
        select(
            func.avg(Score.score).label("avg_score"),
            func.count(Score.id).label("total_exams"),
            Score.course_id,
        )
        .where(Score.student_id == student_id)
        .group_by(Score.course_id)
    )

    result = await db.execute(score_query)
    stats = result.all()

    course_stats = [
        {
            "course_id": str(s.course_id) if s.course_id else None,
            "avg_score": float(s.avg_score) if s.avg_score else 0,
            "total_exams": s.total_exams,
        }
        for s in stats
    ]

    # 获取学习时长统计
    record_query = select(
        func.sum(LearningRecord.duration).label("total_duration"),
        func.count(LearningRecord.id).label("total_records"),
    ).where(LearningRecord.user_id == student_id)

    record_result = await db.execute(record_query)
    record_stats = record_result.one()

    return success(
        {
            "course_stats": course_stats,
            "learning_stats": {
                "total_duration": record_stats.total_duration or 0,
                "total_records": record_stats.total_records or 0,
            },
        }
    )


# ==================== 个性化推荐 ====================


@router.get("/recommendations/student/{student_id}", response_model=dict)
async def get_personalized_recommendations(
    student_id: UUID,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取个性化学习资源推荐
    基于学生的学习历史和成绩进行智能推荐
    """
    ai_service = AIService(db)

    # 获取学生最近的薄弱科目
    score_query = (
        select(Score.course_id, func.avg(Score.score).label("avg_score"))
        .where(Score.student_id == student_id)
        .group_by(Score.course_id)
        .order_by(func.avg(Score.score))
        .limit(3)
    )
    score_result = await db.execute(score_query)
    weak_courses = score_result.all()

    weak_course_ids = [
        str(wc.course_id) if wc.course_id else "未知"
        for wc in weak_courses
        if wc.avg_score and wc.avg_score < 70
    ]

    # 获取学生的学习偏好
    record_query = (
        select(
            LearningRecord.resource_type, func.count(LearningRecord.id).label("count")
        )
        .where(LearningRecord.user_id == student_id)
        .group_by(LearningRecord.resource_type)
        .order_by(desc("count"))
        .limit(3)
    )
    pref_result = await db.execute(record_query)
    preferences = [
        {"type": p.resource_type, "count": p.count}
        for p in pref_result.all()
        if p.resource_type
    ]

    prompt = f"""
请为学生推荐学习资源：

学生ID: {student_id}
薄弱科目: {weak_course_ids}
学习偏好: {preferences}
推荐数量: {limit}

请生成个性化推荐，格式如下：
[
    {{
        "resource_name": "资源名称",
        "resource_type": "资源类型(视频/文档/练习/课程)",
        "difficulty": "难度(基础/进阶/提高)",
        "reason": "推荐原因",
        "estimated_time": "预计学习时长"
    }}
]
"""

    try:
        result = await ai_service.chat(current_user.id, prompt, None, "deepseek")
        return success(result)
    except Exception:
        # AI服务不可用时返回基础推荐
        basic_recommendations = [
            {
                "resource_name": "薄弱科目基础知识讲解",
                "resource_type": "视频",
                "difficulty": "基础",
                "reason": "针对薄弱科目进行巩固",
                "estimated_time": "30分钟",
            },
            {
                "resource_name": "同步练习题库",
                "resource_type": "练习",
                "difficulty": "进阶",
                "reason": "通过练习提升解题能力",
                "estimated_time": "45分钟",
            },
            {
                "resource_name": "难点突破课程",
                "resource_type": "课程",
                "difficulty": "提高",
                "reason": "攻克学习中的难点",
                "estimated_time": "60分钟",
            },
        ]

        return success(
            {
                "recommendations": basic_recommendations[:limit],
                "weak_courses": weak_course_ids,
                "note": "AI服务未配置，使用基础推荐",
            }
        )


@router.get("/recommendations/course/{course_id}", response_model=dict)
async def get_course_recommendations(
    course_id: UUID,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取课程相关推荐
    为特定课程推荐相关的学习资源
    """
    return success(
        {
            "recommendations": [
                {"name": f"课程相关练习{i}", "type": "练习", "reason": "巩固所学"}
                for i in range(1, limit + 1)
            ],
            "course_id": str(course_id),
        }
    )


# ==================== 能力画像 ====================


@router.get("/ability/{student_id}", response_model=dict)
async def get_ability_profile(
    student_id: str,
    course_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取学生能力画像。

    基于成绩历史分析学生多维能力（计算/逻辑/应用等），
    返回各维度得分、优势/薄弱领域及改进建议。
    """
    ai_service = AIService(db)
    profile = await ai_service.get_ability_profile(student_id, course_id)
    return success(profile.model_dump())


@router.get("/radar/{student_id}", response_model=dict)
async def get_ability_radar(
    student_id: str,
    course_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取能力雷达图数据。

    返回前端 ECharts 雷达图所需的指标数据，
    包含各维度得分及与班级平均的对比。
    """
    ai_service = AIService(db)
    radar = await ai_service.get_ability_radar(student_id, course_id)
    return success(radar.model_dump())


# ==================== 知识图谱 ====================


@router.get("/knowledge-graph/{student_id}", response_model=dict)
async def get_knowledge_graph(
    student_id: UUID,
    course_id: Optional[UUID] = Query(None),
    course_name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取学生知识图谱。

    基于课程结构 + 成绩历史构建知识点层次图，
    标注每个节点的掌握度、前置依赖和学习路径。
    """
    ai_service = AIService(db)
    graph = await ai_service.get_knowledge_graph(student_id, course_id, course_name)
    return success(graph.model_dump())


# ==================== 综合诊断报告 ====================


@router.post("/report", response_model=dict)
async def generate_diagnosis_report(
    request: DiagnosisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    生成综合学习诊断报告。

    整合能力画像、知识图谱、雷达图数据，
    返回完整的诊断结论和改进建议。
    """
    ai_service = AIService(db)
    report = await ai_service.generate_diagnosis_report(
        student_id=request.student_id,
        course_id=request.course_id,
        course_name=request.course_name,
    )
    return success(report.model_dump())
