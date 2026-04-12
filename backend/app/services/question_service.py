"""
题库管理模块 - 业务服务层

提供题目的 CRUD、高级筛选、批量操作、相似度检测等服务
"""
import hashlib
from typing import Optional, List, Tuple, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.exam import Question, QuestionAnnotation, SimilarityCheckRecord
from app.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    QuestionQuery,
    QuestionBatchRequest,
    SimilarityCheckRequest,
    SimilarityCheckResponse,
    SimilarQuestion,
    QuestionStatistics,
    AnnotationCreate,
    AnnotationResponse,
    QuestionDistribution,
    DistributionItem,
)


class QuestionService:
    """题目服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============ CRUD 操作 ============
    
    async def create_question(
        self, 
        data: QuestionCreate, 
        creator_id: Optional[UUID] = None
    ) -> Question:
        """创建题目"""
        question = Question(
            content=data.content,
            question_type=data.question_type,
            options=[opt.model_dump() for opt in data.options] if data.options else None,
            answer=data.answer,
            has_answer=data.has_answer,
            scoring_criteria=[crit.model_dump() for crit in data.scoring_criteria] if data.scoring_criteria else None,
            analysis=data.analysis,
            difficulty=data.difficulty,
            cognitive_level=data.cognitive_level,
            score=data.score,
            knowledge_points=data.knowledge_points,
            error_causes=data.error_causes,
            tags=data.tags,
            source=data.source,
            source_ref=data.source_ref,
            creator_id=creator_id,
            review_status="pending"
        )
        
        # 生成相似度哈希
        question.similarity_hash = self._generate_hash(data.content)
        
        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)
        
        return question
    
    async def get_question_by_id(self, question_id: UUID) -> Optional[Question]:
        """根据ID获取题目"""
        query = select(Question).where(
            and_(
                Question.id == question_id,
                Question.is_deleted == False
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_question_full(self, question_id: UUID) -> Optional[Question]:
        """获取题目（含关联数据）"""
        query = select(Question).options(
            selectinload(Question.annotations)
        ).where(
            and_(
                Question.id == question_id,
                Question.is_deleted == False
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_question(
        self, 
        question_id: UUID, 
        data: QuestionUpdate
    ) -> Optional[Question]:
        """更新题目"""
        question = await self.get_question_by_id(question_id)
        if not question:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        # 处理选项
        if "options" in update_data and update_data["options"]:
            if isinstance(update_data["options"][0], dict):
                update_data["options"] = update_data["options"]
            else:
                update_data["options"] = [opt.model_dump() for opt in update_data["options"]]
        
        # 处理评分标准
        if "scoring_criteria" in update_data and update_data["scoring_criteria"]:
            if isinstance(update_data["scoring_criteria"][0], dict):
                update_data["scoring_criteria"] = update_data["scoring_criteria"]
            else:
                update_data["scoring_criteria"] = [crit.model_dump() for crit in update_data["scoring_criteria"]]
        
        # 更新哈希（如果内容改变）
        if "content" in update_data:
            update_data["similarity_hash"] = self._generate_hash(update_data["content"])
        
        for key, value in update_data.items():
            setattr(question, key, value)
        
        await self.db.commit()
        await self.db.refresh(question)
        
        return question
    
    async def delete_question(self, question_id: UUID) -> bool:
        """软删除题目"""
        question = await self.get_question_by_id(question_id)
        if not question:
            return False
        
        question.is_deleted = True
        await self.db.commit()
        
        return True
    
    async def hard_delete_question(self, question_id: UUID) -> bool:
        """硬删除题目"""
        query = delete(Question).where(Question.id == question_id)
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    # ============ 查询筛选 ============
    
    async def query_questions(self, params: QuestionQuery) -> Tuple[List[Question], int]:
        """多条件查询题目"""
        # 构建查询条件
        conditions = []
        
        if not params.include_deleted:
            conditions.append(Question.is_deleted == False)
        
        if params.question_types:
            conditions.append(Question.question_type.in_(params.question_types))
        
        if params.difficulties:
            conditions.append(Question.difficulty.in_(params.difficulties))
        
        if params.cognitive_levels:
            conditions.append(Question.cognitive_level.in_(params.cognitive_levels))
        
        if params.knowledge_points:
            # JSON 数组包含任意一个知识点
            for kp in params.knowledge_points:
                conditions.append(Question.knowledge_points.contains([kp]))
        
        if params.sources:
            conditions.append(Question.source.in_(params.sources))
        
        if params.review_status:
            conditions.append(Question.review_status == params.review_status)
        
        if params.has_answer is not None:
            conditions.append(Question.has_answer == params.has_answer)
        
        # 关键词搜索
        if params.keyword:
            search_conditions = []
            for field in params.search_fields:
                if hasattr(Question, field):
                    search_conditions.append(
                        getattr(Question, field).ilike(f"%{params.keyword}%")
                    )
            if search_conditions:
                conditions.append(or_(*search_conditions))
        
        # 计数查询
        count_query = select(func.count(Question.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 数据查询
        query = select(Question).where(and_(*conditions))
        
        # 排序
        sort_column = getattr(Question, params.sort_by, Question.created_at)
        if params.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # 分页
        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)
        
        result = await self.db.execute(query)
        questions = result.scalars().all()
        
        return list(questions), total
    
    async def get_questions_by_ids(self, question_ids: List[UUID]) -> List[Question]:
        """根据ID列表批量获取题目"""
        query = select(Question).where(
            and_(
                Question.id.in_(question_ids),
                Question.is_deleted == False
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    # ============ 批量操作 ============
    
    async def batch_delete_questions(self, question_ids: List[UUID]) -> int:
        """批量软删除"""
        query = update(Question).where(
            and_(
                Question.id.in_(question_ids),
                Question.is_deleted == False
            )
        ).values(is_deleted=True)
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount
    
    async def batch_update_status(
        self, 
        question_ids: List[UUID],
        status: str,
        reviewer_id: Optional[UUID] = None,
        comment: Optional[str] = None
    ) -> int:
        """批量更新审核状态"""
        update_data = {
            "review_status": status,
            "updated_at": datetime.now()
        }
        if reviewer_id:
            update_data["reviewed_by"] = reviewer_id
            update_data["reviewed_at"] = datetime.now()
        if comment:
            update_data["review_comment"] = comment
        
        query = update(Question).where(
            and_(
                Question.id.in_(question_ids),
                Question.is_deleted == False
            )
        ).values(**update_data)
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount
    
    # ============ 相似度检测 ============
    
    async def check_similarity(
        self, 
        request: SimilarityCheckRequest,
        exclude_ids: Optional[List[UUID]] = None
    ) -> SimilarityCheckResponse:
        """检测题目相似度"""
        content_hash = self._generate_hash(request.content)
        
        # 查询可能相似的题目
        query = select(Question).where(
            and_(
                Question.is_deleted == False,
                Question.similarity_hash.isnot(None)
            )
        )
        
        if exclude_ids:
            query = query.where(Question.id.notin_(exclude_ids))
        
        result = await self.db.execute(query)
        all_questions = result.scalars().all()
        
        similar_questions = []
        max_similarity = 0.0
        
        for q in all_questions:
            if q.similarity_hash:
                similarity = self._calculate_similarity(
                    content_hash, 
                    q.similarity_hash
                )
                if similarity >= request.threshold:
                    similar_questions.append(SimilarQuestion(
                        id=q.id,
                        content=q.content[:200] + "..." if len(q.content) > 200 else q.content,
                        similarity_score=similarity,
                        knowledge_points=q.knowledge_points or []
                    ))
                    max_similarity = max(max_similarity, similarity)
        
        return SimilarityCheckResponse(
            is_duplicate=len(similar_questions) > 0,
            similarity_score=max_similarity,
            similar_questions=sorted(
                similar_questions, 
                key=lambda x: x.similarity_score, 
                reverse=True
            )[:5]  # 最多返回5个最相似的
        )
    
    async def save_similarity_record(
        self,
        content: str,
        threshold: float,
        result: SimilarityCheckResponse,
        checked_by: Optional[UUID] = None
    ) -> SimilarityCheckRecord:
        """保存相似度检测记录"""
        record = SimilarityCheckRecord(
            content_hash=self._generate_hash(content),
            content_preview=content[:200],
            is_duplicate=result.is_duplicate,
            similarity_score=result.similarity_score,
            similar_question_ids=[str(q.id) for q in result.similar_questions],
            threshold=threshold,
            checked_by=checked_by
        )
        
        self.db.add(record)
        await self.db.commit()
        
        return record
    
    # ============ 题目标注 ============
    
    async def add_annotation(
        self,
        question_id: UUID,
        data: AnnotationCreate,
        annotated_by: Optional[UUID] = None
    ) -> QuestionAnnotation:
        """添加题目标注"""
        annotation = QuestionAnnotation(
            question_id=question_id,
            annotation_type=data.annotation_type,
            key=data.key,
            value=data.value,
            confidence=data.confidence,
            annotated_by=annotated_by,
            annotation_method=data.annotation_method
        )
        
        self.db.add(annotation)
        await self.db.commit()
        await self.db.refresh(annotation)
        
        return annotation
    
    async def get_annotations(
        self, 
        question_id: UUID,
        annotation_type: Optional[str] = None
    ) -> List[QuestionAnnotation]:
        """获取题目的标注"""
        query = select(QuestionAnnotation).where(
            QuestionAnnotation.question_id == question_id
        )
        
        if annotation_type:
            query = query.where(
                QuestionAnnotation.annotation_type == annotation_type
            )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def delete_annotation(self, annotation_id: UUID) -> bool:
        """删除标注"""
        query = delete(QuestionAnnotation).where(
            QuestionAnnotation.id == annotation_id
        )
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    # ============ 统计 ============
    
    async def get_statistics(self) -> QuestionStatistics:
        """获取题库统计"""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 总数
        total_query = select(func.count(Question.id)).where(
            Question.is_deleted == False
        )
        total_result = await self.db.execute(total_query)
        total_count = total_result.scalar() or 0
        
        # 今日新增
        today_query = select(func.count(Question.id)).where(
            and_(
                Question.is_deleted == False,
                Question.created_at >= today_start
            )
        )
        today_result = await self.db.execute(today_query)
        today_count = today_result.scalar() or 0
        
        # 待审核
        pending_query = select(func.count(Question.id)).where(
            and_(
                Question.is_deleted == False,
                Question.review_status == "pending"
            )
        )
        pending_result = await self.db.execute(pending_query)
        pending_count = pending_result.scalar() or 0
        
        # 按题型分布
        by_type = await self._get_distribution("question_type")
        
        # 按难度分布
        by_difficulty = await self._get_distribution("difficulty")
        
        # 按认知层级分布
        by_cognitive = await self._get_distribution("cognitive_level")
        
        # 按来源分布
        by_source = await self._get_distribution("source")
        
        return QuestionStatistics(
            total_count=total_count,
            today_count=today_count,
            pending_count=pending_count,
            by_type=by_type,
            by_difficulty=by_difficulty,
            by_cognitive_level=by_cognitive,
            by_source=by_source
        )
    
    async def get_distribution_by_type(self) -> List[dict]:
        """按题型获取分布"""
        return await self._get_distribution("question_type")
    
    async def get_distribution_by_difficulty(self) -> List[dict]:
        """按难度获取分布"""
        return await self._get_distribution("difficulty")
    
    async def _get_distribution(self, field: str) -> List[dict]:
        """获取字段分布统计"""
        query = select(
            getattr(Question, field).label("category"),
            func.count(Question.id).label("count")
        ).where(
            and_(
                Question.is_deleted == False,
                getattr(Question, field).isnot(None)
            )
        ).group_by(getattr(Question, field))
        
        result = await self.db.execute(query)
        rows = result.all()
        
        # 计算总数
        total = sum(row.count for row in rows)
        
        return [
            {
                "category": str(row.category) if row.category else "未分类",
                "count": row.count,
                "percentage": round(row.count / total * 100, 2) if total > 0 else 0
            }
            for row in rows
        ]
    
    # ============ 辅助方法 ============
    
    def _generate_hash(self, content: str) -> str:
        """生成内容哈希"""
        # 简单哈希，可替换为 SimHash 或 TF-IDF
        normalized = content.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _calculate_similarity(self, hash1: str, hash2: str) -> float:
        """计算哈希相似度"""
        if len(hash1) != len(hash2):
            return 0.0
        
        # Hamming 距离
        distance = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
        similarity = 1 - (distance / len(hash1))
        
        return round(similarity, 4)
