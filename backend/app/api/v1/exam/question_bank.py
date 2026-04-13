"""
题库管理 API

提供题目的 CRUD、高级筛选、批量操作、相似度检测等 RESTful 接口
"""
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.question_service import QuestionService
from app.schemas.response import success
from app.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionListResponse,
    QuestionQuery,
    QuestionBatchRequest,
    BatchDeleteRequest,
    BatchUpdateStatusRequest,
    SimilarityCheckRequest,
    SimilarityCheckResponse,
    AnnotationCreate,
    AnnotationResponse,
    QuestionStatistics,
    QuestionDistribution,
    QuestionImportResult,
)

router = APIRouter()


def get_question_service(db: AsyncSession = Depends(get_db)) -> QuestionService:
    """获取题目服务实例"""
    return QuestionService(db)


# ============ 题目 CRUD ============

@router.post("/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    data: QuestionCreate,
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """
    创建题目
    
    - **content**: 题目内容（必填）
    - **question_type**: 题型 single/multiple/fill/essay/calculation
    - **options**: 选择题选项
    - **answer**: 标准答案
    - **difficulty**: 难度 1-5
    - **cognitive_level**: 认知层级 L1-L6
    - **knowledge_points**: 知识点标签列表
    """
    question = await service.create_question(data, creator_id=current_user.id)
    return QuestionResponse.model_validate(question)


@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: UUID,
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """获取题目详情"""
    question = await service.get_question_by_id(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    return QuestionResponse.model_validate(question)


@router.get("/questions", response_model=QuestionListResponse)
async def list_questions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    question_types: Optional[str] = Query(None, description="题型筛选，逗号分隔"),
    difficulties: Optional[str] = Query(None, description="难度筛选，逗号分隔"),
    cognitive_levels: Optional[str] = Query(None, description="认知层级筛选"),
    knowledge_points: Optional[str] = Query(None, description="知识点筛选"),
    sources: Optional[str] = Query(None, description="来源筛选"),
    review_status: Optional[str] = Query(None, description="审核状态"),
    has_answer: Optional[bool] = Query(None),
    keyword: Optional[str] = Query(None, max_length=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """
    查询题目列表（支持多条件筛选）
    
    - **page**: 页码
    - **page_size**: 每页数量
    - **question_types**: 题型筛选 (single, multiple, fill, essay, calculation)
    - **difficulties**: 难度筛选 (1-5)
    - **cognitive_levels**: 认知层级 (L1-L6)
    - **keyword**: 关键词搜索
    """
    # 解析多值参数
    def parse_list(s: Optional[str]) -> Optional[List[str]]:
        if not s:
            return None
        return [x.strip() for x in s.split(",") if x.strip()]
    
    def parse_int_list(s: Optional[str]) -> Optional[List[int]]:
        if not s:
            return None
        return [int(x.strip()) for x in s.split(",") if x.strip()]
    
    query = QuestionQuery(
        page=page,
        page_size=page_size,
        question_types=parse_list(question_types),
        difficulties=parse_int_list(difficulties),
        cognitive_levels=parse_list(cognitive_levels),
        knowledge_points=parse_list(knowledge_points),
        sources=parse_list(sources),
        review_status=review_status,
        has_answer=has_answer,
        keyword=keyword,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    questions, total = await service.query_questions(query)
    
    return QuestionListResponse(
        items=[QuestionResponse.model_validate(q) for q in questions],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: UUID,
    data: QuestionUpdate,
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """更新题目"""
    question = await service.update_question(question_id, data)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    return QuestionResponse.model_validate(question)


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: UUID,
    hard: bool = Query(False, description="是否硬删除"),
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """删除题目（软删除）"""
    if hard:
        success = await service.hard_delete_question(question_id)
    else:
        success = await service.delete_question(question_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    
    return success({"message": "删除成功"})


# ============ 批量操作 ============

@router.post("/questions/batch/delete")
async def batch_delete_questions(
    request: BatchDeleteRequest,
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """批量删除题目"""
    count = await service.batch_delete_questions(request.question_ids)
    return success({"message": f"成功删除 {count} 道题目", "count": count})


@router.post("/questions/batch/update-status")
async def batch_update_status(
    request: BatchUpdateStatusRequest,
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """批量更新审核状态"""
    count = await service.batch_update_status(
        request.question_ids,
        request.review_status,
        reviewer_id=current_user.id,
        comment=request.review_comment
    )
    return success({"message": f"成功更新 {count} 道题目", "count": count})


@router.post("/questions/batch")
async def batch_operation(
    request: QuestionBatchRequest,
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """
    批量操作
    
    - **operation**: import/delete/update_status
    - **question_ids**: 题目ID列表
    - **data**: 操作数据
    - **file**: Base64编码文件（用于导入）
    """
    if request.operation == "delete":
        if not request.question_ids:
            raise HTTPException(status_code=400, detail="缺少题目ID列表")
        count = await service.batch_delete_questions(request.question_ids)
        return success({"message": f"成功删除 {count} 道题目", "count": count})
    
    elif request.operation == "update_status":
        if not request.question_ids:
            raise HTTPException(status_code=400, detail="缺少题目ID列表")
        status_value = request.data.get("review_status") if request.data else None
        if not status_value:
            raise HTTPException(status_code=400, detail="缺少审核状态")
        count = await service.batch_update_status(
            request.question_ids,
            status_value,
            reviewer_id=current_user.id
        )
        return success({"message": f"成功更新 {count} 道题目", "count": count})
    
    else:
        raise HTTPException(status_code=400, detail="不支持的操作类型")


# ============ 相似度检测 ============

@router.post("/questions/similarity/check", response_model=SimilarityCheckResponse)
async def check_similarity(
    request: SimilarityCheckRequest,
    exclude_ids: Optional[str] = Query(None, description="排除的题目ID"),
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """
    检测题目相似度
    
    - **content**: 待检测内容
    - **threshold**: 相似度阈值 (0-1)
    """
    import_uuid = None
    if exclude_ids:
        import_uuid = lambda s: UUID(s.strip())
        exclude_ids = [import_uuid(x) for x in exclude_ids.split(",") if x.strip()]
    
    result = await service.check_similarity(request, exclude_ids=exclude_ids)
    
    # 保存检测记录
    await service.save_similarity_record(
        request.content,
        request.threshold,
        result,
        checked_by=current_user.id
    )
    
    return result


# ============ 题目标注 ============

@router.post("/questions/{question_id}/annotations", response_model=AnnotationResponse)
async def add_annotation(
    question_id: UUID,
    data: AnnotationCreate,
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """添加题目标注"""
    # 检查题目是否存在
    question = await service.get_question_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    annotation = await service.add_annotation(
        question_id,
        data,
        annotated_by=current_user.id
    )
    return AnnotationResponse.model_validate(annotation)


@router.get("/questions/{question_id}/annotations")
async def list_annotations(
    question_id: UUID,
    annotation_type: Optional[str] = Query(None),
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """获取题目的标注列表"""
    annotations = await service.get_annotations(question_id, annotation_type)
    return success([AnnotationResponse.model_validate(a) for a in annotations])


@router.delete("/annotations/{annotation_id}")
async def delete_annotation(
    annotation_id: UUID,
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """删除标注"""
    deleted = await service.delete_annotation(annotation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="标注不存在")
    return success({"message": "删除成功"})


# ============ 统计 ============

@router.get("/questions/statistics/summary")
async def get_statistics(
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """获取题库统计概览"""
    result = await service.get_statistics()
    return success(result)


@router.get("/questions/statistics/distribution")
async def get_distribution(
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """获取题目分布统计"""
    by_type = await service.get_distribution_by_type()
    by_difficulty = await service.get_distribution_by_difficulty()
    
    # TODO: 添加认知层级和来源分布
    result = QuestionDistribution(
        by_type=by_type,
        by_difficulty=by_difficulty,
        by_cognitive_level=[],
        by_source=[]
    )
    return success(result)


@router.get("/questions/statistics/by-type")
async def get_by_type(
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """按题型统计"""
    result = await service.get_distribution_by_type()
    return success(result)


@router.get("/questions/statistics/by-difficulty")
async def get_by_difficulty(
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """按难度统计"""
    result = await service.get_distribution_by_difficulty()
    return success(result)
