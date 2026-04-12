"""
题库质量评分模块 - 业务服务层

提供：
1. AI质量评估 - 多维度题目质量评分
2. 评分管理 - 查询、更新、统计
3. 审核队列 - 待审核题目管理
4. 批量评估 - 批量AI评分
"""
import json
import time
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quality_score import (
    QuestionQualityScore, 
    QualityReviewRecord,
    QualityLevel,
    ApprovalSuggestion,
    EvaluationMode,
)
from app.models.exam import Question
from app.schemas.quality import (
    QualityEvaluationRequest,
    QualityEvaluationResponse,
    DimensionScore,
    QualityScoreQuery,
    QualityScoreItem,
    QualityScoreResponse,
    BatchEvaluateRequest,
    BatchEvaluateResponse,
    BatchEvaluateResult,
    ReviewQueueQuery,
    ReviewQueueItem,
    ReviewDecision,
    QualityStatistics,
    QualityDistributionItem,
)


class QualityScoreService:
    """题目质量评分服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============ 核心评估方法 ============

    async def evaluate_question(
        self, 
        request: QualityEvaluationRequest,
        evaluated_by: Optional[UUID] = None
    ) -> QuestionQualityScore:
        """
        评估单个题目质量
        
        Args:
            request: 评估请求
            evaluated_by: 评估人ID
            
        Returns:
            QuestionQualityScore: 评分记录
        """
        start_time = time.time()
        
        # 构建评估数据
        question_data = {
            "content": request.question_content,
            "type": request.question_type,
            "options": [opt.model_dump() for opt in request.options] if request.options else None,
            "answer": request.answer,
            "difficulty": request.difficulty,
            "cognitive_level": request.cognitive_level,
            "knowledge_points": request.knowledge_points,
            "has_answer": request.has_answer,
            "scoring_criteria": request.scoring_criteria,
            "source": request.source,
        }
        
        # 调用AI评估
        evaluation = await self._call_ai_evaluation(question_data, request.evaluation_mode)
        
        # 构建评分记录
        score = QuestionQualityScore(
            question_id=request.question_id or UUID(),
            question_content=request.question_content[:500],  # 截取摘要
            question_type=request.question_type,
            difficulty=request.difficulty,
            cognitive_level=request.cognitive_level,
            knowledge_points=request.knowledge_points,
            has_answer=request.has_answer,
            source=request.source,
            
            # 维度评分
            difficulty_score=Decimal(str(evaluation.get("difficulty_score", 0))),
            difficulty_reason=evaluation.get("difficulty_reason"),
            
            clarity_score=Decimal(str(evaluation.get("clarity_score", 0))),
            clarity_reason=evaluation.get("clarity_reason"),
            
            cognitive_score=Decimal(str(evaluation.get("cognitive_score", 0))),
            cognitive_level_evaluated=evaluation.get("cognitive_level_evaluated"),
            cognitive_reason=evaluation.get("cognitive_reason"),
            
            discrimination_score=Decimal(str(evaluation.get("discrimination_score", 0))),
            discrimination_reason=evaluation.get("discrimination_reason"),
            
            authenticity_score=Decimal(str(evaluation.get("authenticity_score", 0))),
            authenticity_reason=evaluation.get("authenticity_reason"),
            
            answer_score=Decimal(str(evaluation.get("answer_score", 0))),
            answer_reason=evaluation.get("answer_reason"),
            
            # 综合评分
            overall_score=Decimal(str(evaluation.get("overall_score", 0))),
            quality_level=self.calculate_quality_level(evaluation.get("overall_score", 0)),
            quality_suggestion=evaluation.get("quality_suggestion"),
            approval_suggestion=self.determine_approval_suggestion(evaluation.get("overall_score", 0)),
            
            # 评估信息
            evaluation_mode=request.evaluation_mode,
            evaluation_model=evaluation.get("model", "gpt-4"),
            evaluation_tokens=evaluation.get("tokens", 0),
            evaluation_time_ms=int((time.time() - start_time) * 1000),
        )
        
        self.db.add(score)
        await self.db.commit()
        await self.db.refresh(score)
        
        return score

    async def _call_ai_evaluation(
        self, 
        question_data: Dict, 
        mode: str
    ) -> Dict[str, Any]:
        """
        调用AI进行质量评估
        
        实际项目中应调用LLM API，这里返回模拟结果
        """
        # 构建提示词
        prompt = self.build_evaluation_prompt(question_data, mode)
        
        # TODO: 实际调用 LLM API
        # 这里返回模拟评估结果
        evaluation = self._simulate_evaluation(question_data, prompt)
        
        return evaluation

    def _simulate_evaluation(
        self, 
        question_data: Dict, 
        prompt: str
    ) -> Dict[str, Any]:
        """
        模拟AI评估结果
        
        实际项目中替换为真实LLM调用
        """
        content = question_data.get("content", "")
        qtype = question_data.get("type", "single")
        difficulty = question_data.get("difficulty", 2)
        has_answer = question_data.get("has_answer", True)
        
        # 模拟评分逻辑
        # 基础分数
        base_score = 0.75 + (0.05 * (5 - difficulty))  # 难度低则分数高
        base_score = min(base_score, 0.95)  # 不超过0.95
        
        # 随机波动
        import random
        variance = random.uniform(-0.1, 0.1)
        
        difficulty_score = base_score + variance
        clarity_score = base_score + random.uniform(-0.05, 0.05)
        cognitive_score = base_score + random.uniform(-0.05, 0.05)
        discrimination_score = base_score + random.uniform(-0.1, 0.05)
        authenticity_score = 0.95 + random.uniform(-0.05, 0.05)
        answer_score = 0.90 if has_answer else 0.0
        
        # 计算综合分数
        overall_score = (
            difficulty_score * 0.15 +
            clarity_score * 0.20 +
            cognitive_score * 0.20 +
            discrimination_score * 0.15 +
            authenticity_score * 0.10 +
            answer_score * 0.20
        )
        
        return {
            "difficulty_score": round(difficulty_score, 2),
            "difficulty_reason": "难度适中" if 0.7 <= difficulty_score <= 0.9 else "难度偏高或偏低",
            
            "clarity_score": round(clarity_score, 2),
            "clarity_reason": "表述清晰准确" if clarity_score >= 0.8 else "表述有待改进",
            
            "cognitive_score": round(cognitive_score, 2),
            "cognitive_level_evaluated": question_data.get("cognitive_level", "L2"),
            "cognitive_reason": "认知层级设置合理",
            
            "discrimination_score": round(discrimination_score, 2),
            "discrimination_reason": "区分度良好" if discrimination_score >= 0.7 else "区分度一般",
            
            "authenticity_score": round(authenticity_score, 2),
            "authenticity_reason": "题目原创，无版权问题",
            
            "answer_score": round(answer_score, 2),
            "answer_reason": "答案准确" if has_answer else "开放题，无标准答案",
            
            "overall_score": round(overall_score, 2),
            "quality_suggestion": "可直接使用" if overall_score >= 0.8 else "建议优化后使用",
            
            "model": "gpt-4",
            "tokens": 500,
        }

    def build_evaluation_prompt(
        self, 
        question_data: Dict, 
        mode: str
    ) -> str:
        """
        构建质量评估提示词
        
        Args:
            question_data: 题目数据
            mode: 评估模式 (standard/strict)
        """
        content = question_data.get("content", "")
        qtype = question_data.get("type", "")
        options = question_data.get("options")
        answer = question_data.get("answer")
        difficulty = question_data.get("difficulty", 2)
        cognitive = question_data.get("cognitive_level", "L2")
        
        # 构建选项文本
        options_text = ""
        if options:
            options_text = "\n".join([f"{opt['key']}. {opt['text']}" for opt in options])
        
        strict_note = ""
        if mode == "strict":
            strict_note = "\n【严格模式】评估标准提高20%，低分项更容易出现。"
        
        prompt = f"""
【题目质量评估】

请对以下题目进行多维度质量评估：

题目内容：{content}
题型：{qtype}
{options_text}
答案：{answer or '无标准答案（开放题）'}
预设难度：{difficulty}
认知层级：{cognitive}

【评估维度】

1. 难度适当性 (difficulty_score): 0-1
   - 评估题目难度是否适中，与预设难度是否匹配
   
2. 表述清晰度 (clarity_score): 0-1
   - 评估题目表述是否清晰、无歧义、用词准确
   
3. 认知层级匹配 (cognitive_score): 0-1
   - 评估题目是否有效测试目标认知层级
   
4. 区分度 (discrimination_score): 0-1
   - 评估题目能否有效区分不同水平的学生
   
5. 原创性 (authenticity_score): 0-1
   - 评估题目是否为原创，不存在抄袭或改编问题
   
6. 答案准确性 (answer_score): 0-1
   - 评估答案是否正确，评分标准是否合理{strict_note}

【输出格式】

请以JSON格式输出评估结果：
{{
    "difficulty_score": 0.85,
    "difficulty_reason": "评估理由",
    "clarity_score": 0.90,
    "clarity_reason": "评估理由",
    "cognitive_score": 0.88,
    "cognitive_reason": "评估理由",
    "discrimination_score": 0.75,
    "discrimination_reason": "评估理由",
    "authenticity_score": 0.95,
    "authenticity_reason": "评估理由",
    "answer_score": 0.92,
    "answer_reason": "评估理由",
    "overall_score": 0.88,
    "quality_suggestion": "改进建议"
}}
"""
        return prompt.strip()

    def parse_evaluation_response(self, response_text: str) -> Dict[str, Any]:
        """解析AI评估响应"""
        try:
            # 尝试提取JSON
            text = response_text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            return json.loads(text)
        except json.JSONDecodeError:
            # 返回默认值
            return {
                "difficulty_score": 0.5,
                "clarity_score": 0.5,
                "cognitive_score": 0.5,
                "discrimination_score": 0.5,
                "authenticity_score": 0.5,
                "answer_score": 0.5,
                "overall_score": 0.5,
                "quality_suggestion": "评估解析失败"
            }

    def calculate_quality_level(self, score: float) -> str:
        """计算质量等级"""
        if score >= 0.90:
            return "A"
        elif score >= 0.75:
            return "B"
        elif score >= 0.55:
            return "C"
        else:
            return "D"

    def determine_approval_suggestion(self, score: float) -> str:
        """决定审批建议"""
        if score >= 0.90:
            return "auto_approve"
        elif score >= 0.60:
            return "conditional_pass"
        elif score >= 0.40:
            return "needs_review"
        else:
            return "auto_reject"

    # ============ 评分查询 ============

    async def get_quality_score_by_question_id(
        self, 
        question_id: UUID
    ) -> Optional[QuestionQualityScore]:
        """根据题目ID获取评分"""
        query = select(QuestionQualityScore).where(
            QuestionQualityScore.question_id == question_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def query_quality_scores(
        self, 
        params: QualityScoreQuery
    ) -> Tuple[List[QuestionQualityScore], int]:
        """多条件查询评分"""
        conditions = []
        
        if params.quality_levels:
            conditions.append(QuestionQualityScore.quality_level.in_(params.quality_levels))
        
        if params.approval_suggestions:
            conditions.append(
                QuestionQualityScore.approval_suggestion.in_(params.approval_suggestions)
            )
        
        if params.question_types:
            conditions.append(QuestionQualityScore.question_type.in_(params.question_types))
        
        if params.sources:
            conditions.append(QuestionQualityScore.source.in_(params.sources))
        
        if params.min_score is not None:
            conditions.append(
                QuestionQualityScore.overall_score >= Decimal(str(params.min_score))
            )
        
        if params.max_score is not None:
            conditions.append(
                QuestionQualityScore.overall_score <= Decimal(str(params.max_score))
            )
        
        if params.reviewed is not None:
            conditions.append(QuestionQualityScore.reviewed == params.reviewed)
        
        # 计数
        count_query = select(func.count(QuestionQualityScore.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 数据查询
        query = select(QuestionQualityScore).where(and_(*conditions))
        
        # 排序
        sort_column = getattr(QuestionQualityScore, params.sort_by, QuestionQualityScore.created_at)
        if params.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # 分页
        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)
        
        result = await self.db.execute(query)
        scores = list(result.scalars().all())
        
        return scores, total

    # ============ 批量评估 ============

    async def batch_evaluate_questions(
        self, 
        request: BatchEvaluateRequest
    ) -> BatchEvaluateResponse:
        """
        批量评估题目
        
        Args:
            request: 批量评估请求
            
        Returns:
            BatchEvaluateResponse: 批量评估结果
        """
        results = []
        completed = 0
        pending = 0
        failed = 0
        auto_approved = 0
        auto_rejected = 0
        
        for question_id in request.question_ids:
            try:
                # 获取题目
                query = select(Question).where(
                    and_(
                        Question.id == question_id,
                        Question.is_deleted == False
                    )
                )
                result = await self.db.execute(query)
                question = result.scalar_one_or_none()
                
                if not question:
                    results.append(BatchEvaluateResult(
                        question_id=question_id,
                        status="failed",
                        error="题目不存在"
                    ))
                    failed += 1
                    continue
                
                # 检查是否已有评分
                existing_score = await self.get_quality_score_by_question_id(question_id)
                if existing_score and not request.update_existing:
                    results.append(BatchEvaluateResult(
                        question_id=question_id,
                        overall_score=float(existing_score.overall_score),
                        quality_level=existing_score.quality_level,
                        status="skipped"
                    ))
                    pending += 1
                    continue
                
                # 执行评估
                eval_request = QualityEvaluationRequest(
                    question_id=question_id,
                    question_content=question.content,
                    question_type=question.question_type,
                    difficulty=question.difficulty,
                    has_answer=question.has_answer,
                    source=question.source,
                    evaluation_mode=request.evaluation_mode
                )
                
                score = await self.evaluate_question(eval_request)
                
                # 自动审批
                if score.approval_suggestion == "auto_approve":
                    auto_approved += 1
                elif score.approval_suggestion == "auto_reject":
                    auto_rejected += 1
                
                results.append(BatchEvaluateResult(
                    question_id=question_id,
                    overall_score=float(score.overall_score),
                    quality_level=score.quality_level,
                    status="completed"
                ))
                completed += 1
                
            except Exception as e:
                results.append(BatchEvaluateResult(
                    question_id=question_id,
                    status="failed",
                    error=str(e)
                ))
                failed += 1
        
        return BatchEvaluateResponse(
            total=len(request.question_ids),
            completed=completed,
            pending=pending,
            failed=failed,
            auto_approved=auto_approved,
            auto_rejected=auto_rejected,
            results=results
        )

    # ============ 审核队列 ============

    async def get_review_queue(
        self, 
        params: ReviewQueueQuery
    ) -> Tuple[List[ReviewQueueItem], int]:
        """
        获取审核队列
        
        Args:
            params: 查询参数
            
        Returns:
            Tuple[List[ReviewQueueItem], int]: (队列项列表, 总数)
        """
        conditions = [
            QuestionQualityScore.reviewed == False
        ]
        
        if params.quality_levels:
            conditions.append(
                QuestionQualityScore.quality_level.in_(params.quality_levels)
            )
        
        if params.sources:
            conditions.append(QuestionQualityScore.source.in_(params.sources))
        
        # 计数
        count_query = select(func.count(QuestionQualityScore.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 查询数据
        query = select(QuestionQualityScore).where(and_(*conditions))
        
        # 排序：先按优先级，再按质量分数
        if params.sort_by == "priority":
            # 优先级排序：低分优先
            query = query.order_by(QuestionQualityScore.overall_score.asc())
        else:
            sort_column = getattr(QuestionQualityScore, params.sort_by, QuestionQualityScore.created_at)
            if params.sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        
        # 分页
        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)
        
        result = await self.db.execute(query)
        scores = list(result.scalars().all())
        
        # 构建队列项
        items = []
        for idx, score in enumerate(scores):
            items.append(ReviewQueueItem(
                question_id=score.question_id,
                question_content=score.question_content,
                question_type=score.question_type,
                difficulty=score.difficulty,
                source=score.source,
                quality_score_id=score.id,
                quality_score=float(score.overall_score),
                quality_level=score.quality_level,
                dimension_summary={
                    "difficulty": float(score.difficulty_score),
                    "clarity": float(score.clarity_score),
                    "cognitive": float(score.cognitive_score),
                    "discrimination": float(score.discrimination_score),
                },
                priority=self.calculate_priority(score.source, float(score.overall_score)),
                queue_position=offset + idx + 1,
                ai_generated=score.source == "ai",
                created_at=score.created_at
            ))
        
        return items, total

    def calculate_priority(self, source: str, score: float) -> str:
        """计算审核优先级"""
        # AI生成 + 低分 = 高优先级
        if source == "ai" and score < 0.6:
            return "high"
        # 手动录入 + 高分 = 低优先级
        elif source == "manual" and score >= 0.8:
            return "low"
        # 其他 = 正常优先级
        return "normal"

    async def submit_review_decision(
        self, 
        decision: ReviewDecision,
        reviewer_id: UUID
    ) -> bool:
        """
        提交审核决策
        
        Args:
            decision: 审核决策
            reviewer_id: 审核人ID
            
        Returns:
            bool: 是否成功
        """
        # 获取评分记录
        score = await self.get_quality_score_by_question_id(decision.question_id)
        if not score:
            return False
        
        # 记录审核历史
        review_record = QualityReviewRecord(
            quality_score_id=score.id,
            question_id=decision.question_id,
            previous_score=score.overall_score,
            previous_level=score.quality_level,
            previous_decision=score.review_decision,
            new_score=Decimal(str(decision.adjusted_score)) if decision.adjusted_score else score.overall_score,
            new_level=self.calculate_quality_level(decision.adjusted_score) if decision.adjusted_score else score.quality_level,
            decision=decision.decision,
            override_reason=decision.override_reason,
            review_comment=decision.review_comment,
            reviewer_id=reviewer_id
        )
        
        # 更新评分状态
        score.reviewed = True
        score.reviewed_by = reviewer_id
        score.reviewed_at = datetime.now()
        score.review_decision = decision.decision
        score.review_comment = decision.review_comment
        
        if decision.adjusted_score:
            score.overall_score = Decimal(str(decision.adjusted_score))
            score.quality_level = self.calculate_quality_level(decision.adjusted_score)
        
        # 根据审核决定更新题目状态
        question_query = select(Question).where(Question.id == decision.question_id)
        question_result = await self.db.execute(question_query)
        question = question_result.scalar_one_or_none()
        
        if question:
            if decision.decision == "approve":
                question.review_status = "approved"
            elif decision.decision == "reject":
                question.review_status = "rejected"
        
        self.db.add(review_record)
        await self.db.commit()
        
        return True

    # ============ 统计 ============

    async def get_quality_statistics(self) -> QualityStatistics:
        """获取质量统计"""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 总量统计
        total_query = select(func.count(QuestionQualityScore.id))
        total_result = await self.db.execute(total_query)
        total_evaluated = total_result.scalar() or 0
        
        # 待审核
        pending_query = select(func.count(QuestionQualityScore.id)).where(
            QuestionQualityScore.reviewed == False
        )
        pending_result = await self.db.execute(pending_query)
        pending_review = pending_result.scalar() or 0
        
        # 已审核
        reviewed = total_evaluated - pending_review
        
        # 通过率
        approved_query = select(func.count(QuestionQualityScore.id)).where(
            QuestionQualityScore.review_decision == "approve"
        )
        approved_result = await self.db.execute(approved_query)
        approved_count = approved_result.scalar() or 0
        
        pass_rate = (approved_count / reviewed * 100) if reviewed > 0 else 0
        
        # 按等级分布
        by_level = await self._get_distribution("quality_level")
        
        # 按来源分布
        by_source = await self._get_distribution("source")
        
        # 按题型分布
        by_type = await self._get_distribution("question_type")
        
        # 平均分
        avg_query = select(
            func.avg(QuestionQualityScore.overall_score),
            func.avg(QuestionQualityScore.difficulty_score),
            func.avg(QuestionQualityScore.clarity_score),
            func.avg(QuestionQualityScore.cognitive_score),
        )
        avg_result = await self.db.execute(avg_query)
        avg_row = avg_result.one()
        
        return QualityStatistics(
            total_evaluated=total_evaluated,
            pending_review=pending_review,
            reviewed=reviewed,
            pass_rate=round(pass_rate, 2),
            auto_approve_rate=0,  # TODO: 计算
            auto_reject_rate=0,  # TODO: 计算
            by_level=by_level,
            by_source=by_source,
            by_type=by_type,
            avg_overall_score=float(avg_row[0] or 0),
            avg_difficulty_score=float(avg_row[1] or 0),
            avg_clarity_score=float(avg_row[2] or 0),
            avg_cognitive_score=float(avg_row[3] or 0),
            trend={}
        )

    async def _get_distribution(self, field: str) -> List[QualityDistributionItem]:
        """获取字段分布"""
        query = select(
            getattr(QuestionQualityScore, field).label("category"),
            func.count(QuestionQualityScore.id).label("count")
        ).where(
            getattr(QuestionQualityScore, field).isnot(None)
        ).group_by(getattr(QuestionQualityScore, field))
        
        result = await self.db.execute(query)
        rows = result.all()
        
        total = sum(row.count for row in rows)
        
        return [
            QualityDistributionItem(
                category=str(row.category) if row.category else "未知",
                count=row.count,
                percentage=round(row.count / total * 100, 2) if total > 0 else 0
            )
            for row in rows
        ]
