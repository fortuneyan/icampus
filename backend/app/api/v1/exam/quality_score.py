"""
题库质量评分模块 - API 端点

提供：
1. 质量评估 API - POST /quality/evaluate
2. 评分查询 API - GET /quality/scores
3. 批量评估 API - POST /quality/batch-evaluate
4. 审核队列 API - GET /quality/review-queue
5. 审核决策 API - POST /quality/review
6. 质量统计 API - GET /quality/statistics
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.quality_score_service import QualityScoreService
from app.schemas.response import success
from app.schemas.quality import (
    QualityEvaluationRequest,
    QualityEvaluationResponse,
    DimensionScore,
    QualityScoreQuery,
    QualityScoreResponse,
    QualityScoreListResponse,
    BatchEvaluateRequest,
    BatchEvaluateResponse,
    ReviewQueueQuery,
    ReviewQueueResponse,
    ReviewDecision,
    ReviewDecisionResponse,
    QualityStatistics,
)


# 创建路由器
router = APIRouter(prefix="/quality", tags=["题库质量评分"])


# ============ 依赖注入 ============


async def get_quality_service(
    db: AsyncSession = Depends(get_db),
) -> QualityScoreService:
    """获取质量评分服务"""
    return QualityScoreService(db)


# ============ 质量评估 ============


@router.post(
    "/evaluate",
    response_model=QualityEvaluationResponse,
    summary="评估题目质量",
    description="对单个题目进行AI质量评估，返回多维度评分",
)
async def evaluate_question(
    request: QualityEvaluationRequest,
    service: QualityScoreService = Depends(get_quality_service),
):
    """
    评估题目质量

    - **question_content**: 题目内容
    - **question_type**: 题型 (single/multiple/fill/essay/calculation)
    - **options**: 选择题选项（可选）
    - **answer**: 标准答案（可选）
    - **difficulty**: 预设难度 1-5
    - **cognitive_level**: 认知层级 L1-L6
    - **evaluation_mode**: 评估模式 (standard/strict)

    返回：
    - **overall_score**: 综合评分 0-1
    - **quality_level**: 质量等级 A/B/C/D
    - **dimension_scores**: 各维度评分
    - **approval_suggestion**: 入库建议
    """
    try:
        score = await service.evaluate_question(request)

        return QualityEvaluationResponse(
            quality_score_id=score.id,
            overall_score=float(score.overall_score),
            quality_level=score.quality_level,
            dimension_scores={
                "difficulty": DimensionScore(
                    score=float(score.difficulty_score),
                    reason=score.difficulty_reason or "",
                ),
                "clarity": DimensionScore(
                    score=float(score.clarity_score), reason=score.clarity_reason or ""
                ),
                "cognitive": DimensionScore(
                    score=float(score.cognitive_score),
                    reason=score.cognitive_reason or "",
                ),
                "discrimination": DimensionScore(
                    score=float(score.discrimination_score),
                    reason=score.discrimination_reason or "",
                ),
                "authenticity": DimensionScore(
                    score=float(score.authenticity_score),
                    reason=score.authenticity_reason or "",
                ),
                "answer": DimensionScore(
                    score=float(score.answer_score), reason=score.answer_reason or ""
                ),
            },
            quality_suggestion=score.quality_suggestion,
            approval_suggestion=score.approval_suggestion,
            evaluation_mode=score.evaluation_mode,
            evaluation_model=score.evaluation_model,
            evaluation_time_ms=score.evaluation_time_ms,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评估失败: {str(e)}")


# ============ 评分查询 ============


@router.get(
    "/scores",
    response_model=QualityScoreListResponse,
    summary="查询评分列表",
    description="多条件筛选查询质量评分列表",
)
async def query_quality_scores(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    quality_levels: Optional[str] = Query(None, description="质量等级,逗号分隔"),
    question_types: Optional[str] = Query(None, description="题型,逗号分隔"),
    sources: Optional[str] = Query(None, description="来源,逗号分隔"),
    min_score: Optional[float] = Query(None, ge=0, le=1, description="最低评分"),
    max_score: Optional[float] = Query(None, ge=0, le=1, description="最高评分"),
    reviewed: Optional[bool] = Query(None, description="是否已审核"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="排序方向"),
    service: QualityScoreService = Depends(get_quality_service),
):
    """查询质量评分列表"""

    # 解析逗号分隔的参数
    def parse_list(s: str) -> Optional[list]:
        if not s:
            return None
        return [x.strip() for x in s.split(",") if x.strip()]

    query = QualityScoreQuery(
        page=page,
        page_size=page_size,
        quality_levels=parse_list(quality_levels),
        question_types=parse_list(question_types),
        sources=parse_list(sources),
        min_score=min_score,
        max_score=max_score,
        reviewed=reviewed,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    scores, total = await service.query_quality_scores(query)

    return QualityScoreListResponse(
        items=[
            QualityScoreItem(
                id=s.id,
                question_id=s.question_id,
                question_content=s.question_content,
                question_type=s.question_type,
                difficulty=s.difficulty,
                overall_score=float(s.overall_score),
                quality_level=s.quality_level,
                difficulty_score=float(s.difficulty_score),
                clarity_score=float(s.clarity_score),
                cognitive_score=float(s.cognitive_score),
                discrimination_score=float(s.discrimination_score),
                authenticity_score=float(s.authenticity_score),
                answer_score=float(s.answer_score),
                approval_suggestion=s.approval_suggestion,
                quality_suggestion=s.quality_suggestion,
                source=s.source,
                reviewed=s.reviewed,
                reviewed_by=s.reviewed_by,
                reviewed_at=s.reviewed_at,
                evaluation_model=s.evaluation_model,
                created_at=s.created_at,
            )
            for s in scores
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.get(
    "/scores/{question_id}",
    response_model=QualityScoreResponse,
    summary="获取评分详情",
    description="根据题目ID获取质量评分详情",
)
async def get_quality_score(
    question_id: UUID, service: QualityScoreService = Depends(get_quality_service)
):
    """获取质量评分详情"""
    score = await service.get_quality_score_by_question_id(question_id)

    if not score:
        raise HTTPException(status_code=404, detail="评分记录不存在")

    return QualityScoreResponse(
        id=score.id,
        question_id=score.question_id,
        question_content=score.question_content,
        question_type=score.question_type,
        difficulty=score.difficulty,
        cognitive_level=score.cognitive_level,
        knowledge_points=score.knowledge_points,
        has_answer=score.has_answer,
        source=score.source,
        difficulty_score=float(score.difficulty_score),
        difficulty_reason=score.difficulty_reason,
        clarity_score=float(score.clarity_score),
        clarity_reason=score.clarity_reason,
        cognitive_score=float(score.cognitive_score),
        cognitive_level_evaluated=score.cognitive_level_evaluated,
        cognitive_reason=score.cognitive_reason,
        discrimination_score=float(score.discrimination_score),
        discrimination_reason=score.discrimination_reason,
        authenticity_score=float(score.authenticity_score),
        authenticity_reason=score.authenticity_reason,
        answer_score=float(score.answer_score),
        answer_reason=score.answer_reason,
        overall_score=float(score.overall_score),
        quality_level=score.quality_level,
        quality_suggestion=score.quality_suggestion,
        approval_suggestion=score.approval_suggestion,
        evaluation_mode=score.evaluation_mode,
        evaluation_model=score.evaluation_model,
        evaluation_tokens=score.evaluation_tokens,
        evaluation_time_ms=score.evaluation_time_ms,
        reviewed=score.reviewed,
        reviewed_by=score.reviewed_by,
        reviewed_at=score.reviewed_at,
        review_decision=score.review_decision,
        review_comment=score.review_comment,
        created_at=score.created_at,
        updated_at=score.updated_at,
    )


# ============ 批量评估 ============


@router.post(
    "/batch-evaluate",
    response_model=BatchEvaluateResponse,
    summary="批量评估",
    description="批量对多个题目进行质量评估",
)
async def batch_evaluate(
    request: BatchEvaluateRequest,
    service: QualityScoreService = Depends(get_quality_service),
):
    """
    批量评估题目

    - **question_ids**: 题目ID列表（最多100个）
    - **evaluation_mode**: 评估模式
    - **auto_approve_threshold**: 自动通过阈值（>=此分数自动通过）
    - **auto_reject_threshold**: 自动拒绝阈值（<此分数自动拒绝）
    - **update_existing**: 是否更新已有评分

    返回：
    - **total**: 总数
    - **completed**: 完成数
    - **failed**: 失败数
    - **auto_approved**: 自动通过数
    - **auto_rejected**: 自动拒绝数
    """
    try:
        result = await service.batch_evaluate_questions(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量评估失败: {str(e)}")


# ============ 审核队列 ============


@router.get(
    "/review-queue",
    response_model=ReviewQueueResponse,
    summary="获取审核队列",
    description="获取待审核题目队列",
)
async def get_review_queue(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    priority: Optional[str] = Query(
        None, pattern="^(high|normal|low)$", description="优先级"
    ),
    quality_levels: Optional[str] = Query(None, description="质量等级,逗号分隔"),
    sources: Optional[str] = Query(None, description="来源,逗号分隔"),
    service: QualityScoreService = Depends(get_quality_service),
):
    """获取审核队列"""

    def parse_list(s: str) -> Optional[list]:
        if not s:
            return None
        return [x.strip() for x in s.split(",") if x.strip()]

    query = ReviewQueueQuery(
        page=page,
        page_size=page_size,
        priority=priority,
        quality_levels=parse_list(quality_levels),
        sources=parse_list(sources),
    )

    items, total = await service.get_review_queue(query)

    return ReviewQueueResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.post(
    "/review",
    response_model=ReviewDecisionResponse,
    summary="提交审核决策",
    description="对题目质量评分进行人工审核",
)
async def submit_review(
    decision: ReviewDecision,
    service: QualityScoreService = Depends(get_quality_service),
):
    """
    提交审核决策

    - **question_id**: 题目ID
    - **decision**: 审核决定 (approve/reject/revise)
    - **review_comment**: 审核意见
    - **adjusted_score**: 调整后评分（可选）
    - **override_reason**: 调整原因（可选）
    """
    # TODO: 从认证信息获取审核人ID
    reviewer_id = UUID("00000000-0000-0000-0000-000000000001")

    try:
        success = await service.submit_review_decision(decision, reviewer_id)

        if not success:
            raise HTTPException(status_code=404, detail="评分记录不存在")

        return ReviewDecisionResponse(
            success=True,
            question_id=decision.question_id,
            decision=decision.decision,
            message=f"审核决策 '{decision.decision}' 已提交",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"审核失败: {str(e)}")


# ============ 质量统计 ============


@router.get(
    "/statistics",
    summary="获取质量统计",
    description="获取题库质量评分统计信息",
)
async def get_quality_statistics(
    service: QualityScoreService = Depends(get_quality_service),
):
    """获取质量统计"""
    result = await service.get_quality_statistics()
    return success(result)
