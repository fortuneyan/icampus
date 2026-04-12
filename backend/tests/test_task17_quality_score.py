"""
T17 测试：AI题目质量评分系统

使用 Mock 避免 SQLAlchemy 模型导入冲突
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from decimal import Decimal


class TestQualityScoreSchema:
    """质量评分 Schema 测试"""

    def setup_method(self):
        import sys
        mods = [k for k in sys.modules.keys() if 'app.schemas.quality' in k]
        for m in mods:
            sys.modules.pop(m, None)

    def test_quality_evaluation_request_schema(self):
        """测试：质量评估请求 Schema"""
        from app.schemas.quality import QualityEvaluationRequest
        
        data = {
            "question_id": str(uuid4()),
            "question_content": "测试题目内容",
            "question_type": "single",
            "options": [
                {"key": "A", "text": "选项1"},
                {"key": "B", "text": "选项2"}
            ],
            "answer": "A",
            "difficulty": 2,
            "cognitive_level": "L3",
            "knowledge_points": ["数学", "代数"],
            "has_answer": True,
            "evaluation_mode": "standard"
        }
        
        schema = QualityEvaluationRequest(**data)
        assert schema.question_content == "测试题目内容"
        assert schema.question_type == "single"
        assert schema.evaluation_mode == "standard"
        assert len(schema.options) == 2

    def test_quality_evaluation_request_schema_strict_mode(self):
        """测试：严格模式评估请求"""
        from app.schemas.quality import QualityEvaluationRequest
        
        data = {
            "question_content": "严格测试题目",
            "question_type": "essay",
            "evaluation_mode": "strict"
        }
        
        schema = QualityEvaluationRequest(**data)
        assert schema.evaluation_mode == "strict"
        assert schema.question_type == "essay"

    def test_quality_evaluation_request_schema_invalid_mode(self):
        """测试：无效评估模式"""
        from app.schemas.quality import QualityEvaluationRequest
        from pydantic import ValidationError
        
        data = {
            "question_content": "测试",
            "question_type": "single",
            "evaluation_mode": "invalid_mode"
        }
        
        with pytest.raises(ValidationError):
            QualityEvaluationRequest(**data)

    def test_quality_evaluation_request_schema_minimal(self):
        """测试：最小化评估请求"""
        from app.schemas.quality import QualityEvaluationRequest
        
        data = {
            "question_content": "最简单的题目",
            "question_type": "single"
        }
        
        schema = QualityEvaluationRequest(**data)
        assert schema.question_content == "最简单的题目"
        assert schema.has_answer == True  # 默认值
        assert schema.evaluation_mode == "standard"  # 默认值

    def test_quality_evaluation_request_schema_fill_type(self):
        """测试：填空题请求"""
        from app.schemas.quality import QualityEvaluationRequest
        
        data = {
            "question_content": "北京是中国的_____。",
            "question_type": "fill",
            "answer": "首都",
            "difficulty": 1
        }
        
        schema = QualityEvaluationRequest(**data)
        assert schema.question_type == "fill"
        assert schema.answer == "首都"

    def test_quality_evaluation_response_schema(self):
        """测试：质量评估响应 Schema"""
        from app.schemas.quality import QualityEvaluationResponse, DimensionScore
        
        data = {
            "question_id": str(uuid4()),
            "overall_score": 0.88,
            "quality_level": "B",
            "dimension_scores": {
                "difficulty": DimensionScore(score=0.85, reason="难度适中"),
                "clarity": DimensionScore(score=0.90, reason="表述清晰"),
                "cognitive": DimensionScore(score=0.88, reason="认知层级准确"),
                "discrimination": DimensionScore(score=0.80, reason="区分度良好"),
                "authenticity": DimensionScore(score=0.95, reason="原创"),
                "answer": DimensionScore(score=0.92, reason="答案准确"),
            },
            "quality_suggestion": "建议优化",
            "approval_suggestion": "conditional_pass",
            "evaluation_mode": "standard"
        }
        
        schema = QualityEvaluationResponse(**data)
        assert schema.overall_score == 0.88
        assert schema.quality_level == "B"
        assert "difficulty" in schema.dimension_scores
        assert schema.approval_suggestion == "conditional_pass"

    def test_batch_evaluate_request_schema(self):
        """测试：批量评估请求 Schema"""
        from app.schemas.quality import BatchEvaluateRequest
        
        data = {
            "question_ids": [str(uuid4()), str(uuid4())],
            "evaluation_mode": "standard",
            "auto_approve_threshold": 0.90,
            "auto_reject_threshold": 0.40
        }
        
        schema = BatchEvaluateRequest(**data)
        assert len(schema.question_ids) == 2
        assert schema.auto_approve_threshold == 0.90
        assert schema.auto_reject_threshold == 0.40
        assert schema.update_existing == True  # 默认值

    def test_batch_evaluate_response_schema(self):
        """测试：批量评估响应 Schema"""
        from app.schemas.quality import BatchEvaluateResponse, BatchEvaluateResult
        
        data = {
            "total": 10,
            "completed": 8,
            "pending": 2,
            "failed": 0,
            "auto_approved": 3,
            "auto_rejected": 1,
            "results": [
                BatchEvaluateResult(
                    question_id=uuid4(),
                    overall_score=0.85,
                    quality_level="B",
                    status="completed"
                )
            ]
        }
        
        schema = BatchEvaluateResponse(**data)
        assert schema.total == 10
        assert schema.completed == 8
        assert schema.auto_approved == 3
        assert schema.auto_rejected == 1
        assert len(schema.results) == 1

    def test_review_queue_item_schema(self):
        """测试：审核队列项 Schema"""
        from app.schemas.quality import ReviewQueueItem
        
        data = {
            "question_id": str(uuid4()),
            "question_content": "待审核题目",
            "question_type": "single",
            "difficulty": 2,
            "source": "ai",
            "quality_score_id": str(uuid4()),
            "quality_score": 0.78,
            "quality_level": "C",
            "dimension_summary": {"difficulty": 0.80, "clarity": 0.85},
            "priority": "normal",
            "queue_position": 5,
            "ai_generated": True,
            "created_at": datetime.now()
        }
        
        schema = ReviewQueueItem(**data)
        assert schema.quality_level == "C"
        assert schema.priority == "normal"
        assert schema.queue_position == 5
        assert schema.ai_generated == True

    def test_review_decision_schema(self):
        """测试：审核决策 Schema"""
        from app.schemas.quality import ReviewDecision
        
        data = {
            "question_id": str(uuid4()),
            "decision": "approve",
            "review_comment": "题目质量良好，同意入库"
        }
        
        schema = ReviewDecision(**data)
        assert schema.decision == "approve"
        assert schema.review_comment == "题目质量良好，同意入库"

    def test_review_decision_schema_with_adjustment(self):
        """测试：审核决策 Schema - 带评分调整"""
        from app.schemas.quality import ReviewDecision
        
        data = {
            "question_id": str(uuid4()),
            "decision": "revise",
            "review_comment": "调整评分",
            "adjusted_score": 0.85,
            "override_reason": "原评分偏低"
        }
        
        schema = ReviewDecision(**data)
        assert schema.decision == "revise"
        assert schema.adjusted_score == 0.85
        assert schema.override_reason == "原评分偏低"


class TestQualityScoreService:
    """质量评分 Service 测试 (使用 Mock)"""

    @pytest.mark.asyncio
    async def test_calculate_quality_level(self):
        """测试：计算质量等级"""
        # 直接测试 Service 的辅助方法
        from app.services.quality_score_service import QualityScoreService
        
        mock_db = MagicMock()
        service = QualityScoreService(mock_db)
        
        # A级：>=0.9
        assert service.calculate_quality_level(0.92) == "A"
        assert service.calculate_quality_level(0.95) == "A"
        assert service.calculate_quality_level(0.90) == "A"
        
        # B级：>=0.75
        assert service.calculate_quality_level(0.80) == "B"
        assert service.calculate_quality_level(0.75) == "B"
        
        # C级：>=0.55
        assert service.calculate_quality_level(0.60) == "C"
        assert service.calculate_quality_level(0.55) == "C"
        
        # D级：<0.55
        assert service.calculate_quality_level(0.45) == "D"
        assert service.calculate_quality_level(0.54) == "D"
        assert service.calculate_quality_level(0.0) == "D"

    @pytest.mark.asyncio
    async def test_determine_approval_suggestion(self):
        """测试：决定审批建议"""
        from app.services.quality_score_service import QualityScoreService
        
        mock_db = MagicMock()
        service = QualityScoreService(mock_db)
        
        # 自动通过：>=0.9
        assert service.determine_approval_suggestion(0.92) == "auto_approve"
        assert service.determine_approval_suggestion(0.90) == "auto_approve"
        
        # 有条件通过：0.6-0.9
        assert service.determine_approval_suggestion(0.75) == "conditional_pass"
        assert service.determine_approval_suggestion(0.60) == "conditional_pass"
        
        # 需审核：0.4-0.6
        assert service.determine_approval_suggestion(0.50) == "needs_review"
        assert service.determine_approval_suggestion(0.40) == "needs_review"
        
        # 自动拒绝：<0.4
        assert service.determine_approval_suggestion(0.35) == "auto_reject"
        assert service.determine_approval_suggestion(0.0) == "auto_reject"

    @pytest.mark.asyncio
    async def test_build_evaluation_prompt_standard(self):
        """测试：构建标准评估 Prompt"""
        from app.services.quality_score_service import QualityScoreService
        
        mock_db = MagicMock()
        service = QualityScoreService(mock_db)
        
        question = {
            "content": "1+1=?",
            "type": "single",
            "options": [
                {"key": "A", "text": "1"},
                {"key": "B", "text": "2"}
            ],
            "answer": "B",
            "difficulty": 1,
            "cognitive_level": "L1"
        }
        
        prompt = service.build_evaluation_prompt(question, "standard")
        
        assert "1+1=?" in prompt
        assert "single" in prompt.lower()
        assert "评分" in prompt or "评估" in prompt
        assert "B" in prompt  # 答案

    @pytest.mark.asyncio
    async def test_build_evaluation_prompt_strict(self):
        """测试：构建严格评估 Prompt"""
        from app.services.quality_score_service import QualityScoreService
        
        mock_db = MagicMock()
        service = QualityScoreService(mock_db)
        
        question = {
            "content": "证明题内容",
            "type": "essay"
        }
        
        prompt = service.build_evaluation_prompt(question, "strict")
        
        # 严格模式应该包含提示
        assert "严格" in prompt or "strict" in prompt.lower()

    @pytest.mark.asyncio
    async def test_build_evaluation_prompt_without_answer(self):
        """测试：无答案题目 Prompt"""
        from app.services.quality_score_service import QualityScoreService
        
        mock_db = MagicMock()
        service = QualityScoreService(mock_db)
        
        question = {
            "content": "开放性问题",
            "type": "essay",
            "has_answer": False
        }
        
        prompt = service.build_evaluation_prompt(question, "standard")
        
        assert "无" in prompt or "开放" in prompt

    @pytest.mark.asyncio
    async def test_parse_ai_evaluation_response(self):
        """测试：解析AI评估响应"""
        from app.services.quality_score_service import QualityScoreService
        
        mock_db = MagicMock()
        service = QualityScoreService(mock_db)
        
        response_text = '''
        {
            "difficulty_score": 0.85,
            "clarity_score": 0.90,
            "cognitive_score": 0.88,
            "discrimination_score": 0.80,
            "authenticity_score": 0.95,
            "answer_score": 0.92,
            "overall_score": 0.88,
            "quality_level": "B",
            "quality_suggestion": "可使用"
        }
        '''
        
        result = service.parse_evaluation_response(response_text)
        
        assert result["overall_score"] == 0.88
        assert result["quality_level"] == "B"
        assert result["difficulty_score"] == 0.85

    @pytest.mark.asyncio
    async def test_parse_ai_evaluation_response_with_reasons(self):
        """测试：解析含详细理由的响应"""
        from app.services.quality_score_service import QualityScoreService
        
        mock_db = MagicMock()
        service = QualityScoreService(mock_db)
        
        response_text = '''
        {
            "difficulty_score": 0.85,
            "difficulty_reason": "难度适中",
            "clarity_score": 0.90,
            "clarity_reason": "表述清晰",
            "cognitive_score": 0.88,
            "cognitive_reason": "L3层级准确",
            "discrimination_score": 0.80,
            "discrimination_reason": "区分度良好",
            "authenticity_score": 0.95,
            "authenticity_reason": "原创",
            "answer_score": 0.92,
            "answer_reason": "答案准确",
            "overall_score": 0.88,
            "quality_level": "B",
            "quality_suggestion": "可使用"
        }
        '''
        
        result = service.parse_evaluation_response(response_text)
        
        assert result["difficulty_reason"] == "难度适中"
        assert result["clarity_reason"] == "表述清晰"
        assert result["cognitive_reason"] == "L3层级准确"

    @pytest.mark.asyncio
    async def test_parse_invalid_response(self):
        """测试：解析无效响应"""
        from app.services.quality_score_service import QualityScoreService
        
        mock_db = MagicMock()
        service = QualityScoreService(mock_db)
        
        # 无效的 JSON
        result = service.parse_evaluation_response("这不是 JSON")
        
        # 应该返回默认值
        assert result["overall_score"] == 0.5
        assert result["quality_suggestion"] == "评估解析失败"


class TestQualityReviewQueue:
    """审核队列测试"""

    def test_priority_calculation(self):
        """测试：优先级计算"""
        from app.services.quality_score_service import QualityScoreService
        
        mock_db = MagicMock()
        service = QualityScoreService(mock_db)
        
        # AI生成 + 低分 = 高优先级
        priority = service.calculate_priority("ai", 0.45)
        assert priority == "high"
        
        priority = service.calculate_priority("ai", 0.59)
        assert priority == "high"
        
        # 手动录入 + 高分 = 低优先级
        priority = service.calculate_priority("manual", 0.88)
        assert priority == "low"
        
        priority = service.calculate_priority("manual", 0.80)
        assert priority == "low"
        
        # 中等分数 = 正常优先级
        priority = service.calculate_priority("ai", 0.70)
        assert priority == "normal"
        
        priority = service.calculate_priority("reference", 0.50)
        assert priority == "normal"
        
        # AI生成 + 高分 = 正常优先级
        priority = service.calculate_priority("ai", 0.90)
        assert priority == "normal"

    def test_priority_boundary_cases(self):
        """测试：优先级边界情况"""
        from app.services.quality_score_service import QualityScoreService
        
        mock_db = MagicMock()
        service = QualityScoreService(mock_db)
        
        # 边界分数
        assert service.calculate_priority("ai", 0.60) == "normal"
        assert service.calculate_priority("manual", 0.79) == "normal"


class TestQualityLevelEnums:
    """质量等级枚举测试"""

    def test_quality_level_enum(self):
        """测试：质量等级枚举"""
        from app.schemas.quality import QualityLevelEnum
        
        assert QualityLevelEnum.A == "A"
        assert QualityLevelEnum.B == "B"
        assert QualityLevelEnum.C == "C"
        assert QualityLevelEnum.D == "D"

    def test_approval_suggestion_enum(self):
        """测试：审批建议枚举"""
        from app.schemas.quality import ApprovalSuggestionEnum
        
        assert ApprovalSuggestionEnum.AUTO_APPROVE == "auto_approve"
        assert ApprovalSuggestionEnum.CONDITIONAL_PASS == "conditional_pass"
        assert ApprovalSuggestionEnum.NEEDS_REVIEW == "needs_review"
        assert ApprovalSuggestionEnum.AUTO_REJECT == "auto_reject"

    def test_review_priority_enum(self):
        """测试：审核优先级枚举"""
        from app.schemas.quality import ReviewPriorityEnum
        
        assert ReviewPriorityEnum.HIGH == "high"
        assert ReviewPriorityEnum.NORMAL == "normal"
        assert ReviewPriorityEnum.LOW == "low"


class TestDimensionScore:
    """维度评分测试"""

    def test_dimension_score_valid(self):
        """测试：有效维度评分"""
        from app.schemas.quality import DimensionScore
        
        score = DimensionScore(
            score=0.85,
            reason="难度适中"
        )
        
        assert score.score == 0.85
        assert score.reason == "难度适中"

    def test_dimension_score_boundary(self):
        """测试：维度评分边界"""
        from app.schemas.quality import DimensionScore
        from pydantic import ValidationError
        
        # 最小值 0
        score = DimensionScore(score=0.0, reason="最低分")
        assert score.score == 0.0
        
        # 最大值 1
        score = DimensionScore(score=1.0, reason="最高分")
        assert score.score == 1.0

    def test_dimension_score_invalid(self):
        """测试：无效维度评分"""
        from app.schemas.quality import DimensionScore
        from pydantic import ValidationError
        
        # 超出范围
        with pytest.raises(ValidationError):
            DimensionScore(score=1.5, reason="超出范围")
        
        with pytest.raises(ValidationError):
            DimensionScore(score=-0.1, reason="负数")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
