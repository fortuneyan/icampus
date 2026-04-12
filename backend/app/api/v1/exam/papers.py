"""
Smart Paper Generation - API Routes

API endpoints for:
1. Paper generation (greedy, diagnostic, A/B)
2. Paper CRUD management
3. Paper statistics
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.paper import (
    PaperGenerateRequest,
    DiagnosticGenerateRequest,
    ABPaperRequest,
    ABPaperResponse,
    PaperResponse,
    PaperListResponse,
    PaperWithQuestions,
    PaperStatistics,
    PaperUpdate,
    PaperExportFormat,
    PaperExportRequest,
    PaperConstraints,
    PaperGenerationResult,
)
from app.services.paper_service import (
    PaperService,
    GreedyPaperGenerator,
    DiagnosticPaperGenerator,
    ABPaperGenerator,
)
from app.core.database import get_db

router = APIRouter(prefix="/papers", tags=["智能组卷"])


def get_paper_service(db: AsyncSession = Depends(get_db)) -> PaperService:
    """获取试卷服务"""
    return PaperService(db)


# =============================================================================
# Paper Generation Endpoints
# =============================================================================


@router.post("/generate", response_model=PaperGenerationResult, summary="智能组卷")
async def generate_paper(
    request: PaperGenerateRequest,
    service: PaperService = Depends(get_paper_service),
    creator_id: UUID = Query(None, description="创建者ID"),
):
    """
    智能组卷 - 使用贪心算法根据约束条件生成试卷

    支持：
    - 按知识点筛选题目
    - 按难度分布生成
    - 按题型数量生成
    """
    try:
        result = await service.generate_paper(request, creator_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/generate/diagnostic", response_model=PaperGenerationResult, summary="诊断组卷"
)
async def generate_diagnostic_paper(
    request: DiagnosticGenerateRequest,
    service: PaperService = Depends(get_paper_service),
    creator_id: UUID = Query(None, description="创建者ID"),
):
    """
    诊断组卷 - 根据学生诊断报告生成个性化试卷

    根据学生的薄弱知识点和能力水平动态调整难度分布
    """
    try:
        result = await service.generate_diagnostic_paper(request, creator_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/generate/ab-pair", response_model=ABPaperResponse, summary="A/B卷生成")
async def generate_ab_papers(
    request: ABPaperRequest,
    service: PaperService = Depends(get_paper_service),
):
    """
    A/B卷生成 - 基于已有试卷生成配对试卷

    生成与原卷相似但不完全相同的试卷，用于：
    - 防止作弊
    - 平行考试
    """
    try:
        paper_a, paper_b, similarity = await service.generate_ab_papers(request, None)
        return ABPaperResponse(
            paper_a=PaperResponse.model_validate(paper_a),
            paper_b=PaperResponse.model_validate(paper_b),
            similarity_score=similarity,
            questions_replaced=len(paper_b.question_ids),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Paper CRUD Endpoints
# =============================================================================


@router.get("", response_model=PaperListResponse, summary="试卷列表")
async def list_papers(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    subject: Optional[str] = Query(None, description="学科筛选"),
    paper_type: Optional[str] = Query(None, description="试卷类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    service: PaperService = Depends(get_paper_service),
):
    """
    获取试卷列表

    支持分页和多维度筛选
    """
    papers, total = await service.list_papers(
        page=page,
        page_size=page_size,
        subject=subject,
        paper_type=paper_type,
        status=status,
        keyword=keyword,
    )

    return PaperListResponse(
        items=[PaperResponse.model_validate(p) for p in papers],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/statistics", response_model=PaperStatistics, summary="试卷统计")
async def get_statistics(
    service: PaperService = Depends(get_paper_service),
):
    """
    获取试卷统计信息

    返回试卷总数、发布状态分布、类型分布等
    """
    stats = await service.get_statistics()
    return PaperStatistics(**stats)


@router.get("/{paper_id}", response_model=PaperWithQuestions, summary="试卷详情")
async def get_paper(
    paper_id: UUID,
    include_answers: bool = Query(True, description="包含答案"),
    service: PaperService = Depends(get_paper_service),
):
    """
    获取试卷详情

    包含题目列表和答案（如有权限）
    """
    paper_data = await service.get_paper_with_questions(paper_id, include_answers)

    if not paper_data:
        raise HTTPException(status_code=404, detail="试卷不存在")

    return PaperWithQuestions(**paper_data)


@router.put("/{paper_id}", response_model=PaperResponse, summary="更新试卷")
async def update_paper(
    paper_id: UUID,
    request: PaperUpdate,
    service: PaperService = Depends(get_paper_service),
):
    """
    更新试卷信息

    可更新：标题、状态、约束条件、题目列表
    """
    paper = await service.update_paper(paper_id, request)

    if not paper:
        raise HTTPException(status_code=404, detail="试卷不存在")

    return PaperResponse.model_validate(paper)


@router.delete("/{paper_id}", summary="删除试卷")
async def delete_paper(
    paper_id: UUID,
    service: PaperService = Depends(get_paper_service),
):
    """
    删除试卷（软删除）
    """
    success = await service.delete_paper(paper_id)

    if not success:
        raise HTTPException(status_code=404, detail="试卷不存在")

    return {"message": "删除成功"}


@router.post("/{paper_id}/publish", response_model=PaperResponse, summary="发布试卷")
async def publish_paper(
    paper_id: UUID,
    service: PaperService = Depends(get_paper_service),
):
    """
    发布试卷

    发布后试卷状态变为 published
    """
    paper = await service.publish_paper(paper_id)

    if not paper:
        raise HTTPException(status_code=404, detail="试卷不存在")

    return PaperResponse.model_validate(paper)


@router.get("/{paper_id}/detail", response_model=PaperWithQuestions, summary="试卷详情(含题目)")
async def get_paper_detail(
    paper_id: UUID,
    include_answers: bool = Query(True, description="包含答案"),
    service: PaperService = Depends(get_paper_service),
):
    """
    获取试卷详情（含完整题目列表）

    包含题目内容和答案（如有权限）
    """
    paper_data = await service.get_paper_with_questions(paper_id, include_answers)

    if not paper_data:
        raise HTTPException(status_code=404, detail="试卷不存在")

    return PaperWithQuestions(**paper_data)


@router.get("/{paper_id}/export", summary="导出试卷")
async def export_paper(
    paper_id: UUID,
    format: str = Query("json", description="导出格式: json/markdown"),
    include_answers: bool = Query(True, description="包含答案"),
    include_analysis: bool = Query(True, description="包含解析"),
    service: PaperService = Depends(get_paper_service),
):
    """
    导出试卷

    - **format**: 导出格式 json/markdown
    - **include_answers**: 是否包含答案
    - **include_analysis**: 是否包含解析
    """
    paper_data = await service.get_paper_with_questions(paper_id, include_answers)
    if not paper_data:
        raise HTTPException(status_code=404, detail="试卷不存在")

    return paper_data
