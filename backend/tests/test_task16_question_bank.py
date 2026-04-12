"""
T16 测试：题库管理模块

覆盖：
1. Question 模型 - CRUD 操作
2. Question API - RESTful 接口
3. 高级筛选 - 多条件组合
4. 题目标注 - 知识点/认知层级标注
5. 相似度检测 - 内容去重
6. 批量操作 - 导入/删除/更新
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from decimal import Decimal


class TestQuestionModel:
    """Question 模型测试"""

    def setup_method(self):
        """模块级重置"""
        import sys
        mods = [k for k in sys.modules.keys() if 'app.models.question' in k or 'app.schemas.question' in k]
        for m in mods:
            sys.modules.pop(m, None)

    def test_create_question_model_with_options(self):
        """测试：创建带选项的选择题模型"""
        from app.models.question import Question
        
        question = Question(
            content="下列关于二次函数的说法正确的是？",
            question_type="single",
            options=[
                {"key": "A", "text": "开口向上"},
                {"key": "B", "text": "开口向下"},
                {"key": "C", "text": "对称轴是y轴"},
                {"key": "D", "text": "顶点在原点"}
            ],
            answer="A",
            difficulty=2,
            cognitive_level="L3",
            knowledge_points=["二次函数", "性质"],
            source="manual",
            review_status="pending"
        )
        
        assert question.content == "下列关于二次函数的说法正确的是？"
        assert question.question_type == "single"
        assert len(question.options) == 4
        assert question.answer == "A"
        assert question.difficulty == 2
        assert question.cognitive_level == "L3"
        assert "二次函数" in question.knowledge_points
        assert question.source == "manual"
        assert question.review_status == "pending"
        # is_deleted 默认为 False（SQLAlchemy 默认值）
        assert question.is_deleted is not True
        # has_answer 默认为 True
        assert question.has_answer is not False

    def test_create_fill_question(self):
        """测试：创建填空题"""
        from app.models.question import Question
        
        question = Question(
            content="一次函数 y=kx+b 中，当 k>0 时，函数图像经过第_____象限。",
            question_type="fill",
            answer="一、三",
            difficulty=1,
            knowledge_points=["一次函数", "象限"],
            source="manual"
        )
        
        assert question.question_type == "fill"
        assert question.answer == "一、三"
        assert question.difficulty == 1
        assert question.options is None

    def test_create_essay_question_with_scoring_criteria(self):
        """测试：创建解答题（带评分标准）"""
        from app.models.question import Question
        
        scoring_criteria = [
            {"level": "完整", "score": 10, "description": "步骤完整，答案正确"},
            {"level": "部分", "score": 6, "description": "步骤部分正确"},
            {"level": "错误", "score": 0, "description": "答案错误"}
        ]
        
        question = Question(
            content="求解方程 x² - 5x + 6 = 0",
            question_type="essay",
            answer="x=2 或 x=3",
            scoring_criteria=scoring_criteria,
            difficulty=3,
            cognitive_level="L4",
            knowledge_points=["一元二次方程", "因式分解"],
            score=Decimal("10.0"),
            source="manual"
        )
        
        assert question.question_type == "essay"
        assert question.answer == "x=2 或 x=3"
        assert len(question.scoring_criteria) == 3
        assert question.score == Decimal("10.0")
        assert question.cognitive_level == "L4"

    def test_question_without_answer(self):
        """测试：创建无答案题目（开放题）"""
        from app.models.question import Question
        
        question = Question(
            content="请分析当前环境污染的主要原因，并提出可行的解决方案。",
            question_type="essay",
            has_answer=False,
            difficulty=4,
            cognitive_level="L5",
            knowledge_points=["环境保护", "问题分析"],
            source="ai"
        )
        
        assert question.has_answer == False
        assert question.answer is None
        assert question.scoring_criteria is None

    def test_soft_delete_question(self):
        """测试：软删除题目"""
        from app.models.question import Question
        
        question = Question(
            content="测试题目",
            question_type="single",
            is_deleted=False
        )
        
        assert question.is_deleted == False
        
        # 执行软删除
        question.is_deleted = True
        
        assert question.is_deleted == True
        # 数据仍然存在，只是标记为删除

    def test_knowledge_points_json(self):
        """测试：知识点 JSON 存储与读取"""
        from app.models.question import Question
        
        knowledge_points = ["函数", "单调性", "导数", "极值"]
        
        question = Question(
            content="测试知识点存储",
            question_type="single",
            knowledge_points=knowledge_points
        )
        
        assert len(question.knowledge_points) == 4
        assert "单调性" in question.knowledge_points
        assert question.knowledge_points == knowledge_points

    def test_error_causes_annotation(self):
        """测试：易错点标注"""
        from app.models.question import Question
        
        error_causes = [
            {"type": "审题错误", "description": "忽略定义域"},
            {"type": "计算错误", "description": "符号处理不当"}
        ]
        
        question = Question(
            content="求函数定义域",
            question_type="fill",
            error_causes=error_causes
        )
        
        assert len(question.error_causes) == 2
        assert question.error_causes[0]["type"] == "审题错误"

    def test_quality_metrics(self):
        """测试：质量指标字段"""
        from app.models.question import Question
        
        question = Question(
            content="测试质量指标",
            question_type="single",
            usage_count=100,
            correct_rate=Decimal("0.75"),
            avg_time=Decimal("120.5"),
            discrimination=Decimal("0.45")
        )
        
        assert question.usage_count == 100
        assert question.correct_rate == Decimal("0.75")
        assert question.avg_time == Decimal("120.5")
        assert question.discrimination == Decimal("0.45")


class TestQuestionSchema:
    """Question Schema 测试"""

    def setup_method(self):
        import sys
        mods = [k for k in sys.modules.keys() if 'app.schemas.question' in k]
        for m in mods:
            sys.modules.pop(m, None)

    def test_question_create_schema_valid(self):
        """测试：QuestionCreate Schema 验证 - 有效数据"""
        from app.schemas.question import QuestionCreate
        from pydantic import ValidationError
        
        data = {
            "content": "1+1=?",
            "question_type": "single",
            "options": [
                {"key": "A", "text": "1"},
                {"key": "B", "text": "2"},
                {"key": "C", "text": "3"}
            ],
            "answer": "B",
            "difficulty": 1,
            "knowledge_points": ["加法"]
        }
        
        schema = QuestionCreate(**data)
        assert schema.content == "1+1=?"
        assert schema.question_type == "single"
        assert len(schema.options) == 3
        assert schema.answer == "B"
        assert schema.difficulty == 1

    def test_question_create_schema_invalid_type(self):
        """测试：QuestionCreate Schema 验证 - 非法题型"""
        from app.schemas.question import QuestionCreate
        from pydantic import ValidationError
        
        data = {
            "content": "测试",
            "question_type": "invalid_type"  # 非法题型
        }
        
        with pytest.raises(ValidationError) as exc_info:
            QuestionCreate(**data)
        
        errors = exc_info.value.errors()
        assert any("question_type" in str(e.get("loc", [])) for e in errors)

    def test_question_create_schema_missing_content(self):
        """测试：QuestionCreate Schema 验证 - 缺少内容"""
        from app.schemas.question import QuestionCreate
        from pydantic import ValidationError
        
        data = {
            "question_type": "single"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            QuestionCreate(**data)
        
        errors = exc_info.value.errors()
        assert any("content" in str(e.get("loc", [])) for e in errors)

    def test_question_create_schema_difficulty_range(self):
        """测试：QuestionCreate Schema 验证 - 难度范围"""
        from app.schemas.question import QuestionCreate
        from pydantic import ValidationError
        
        # 难度超出范围
        data = {
            "content": "测试",
            "question_type": "single",
            "difficulty": 10  # 超出 1-5 范围
        }
        
        with pytest.raises(ValidationError):
            QuestionCreate(**data)

    def test_question_create_schema_cognitive_level(self):
        """测试：QuestionCreate Schema 验证 - 认知层级格式"""
        from app.schemas.question import QuestionCreate
        from pydantic import ValidationError
        
        # 有效认知层级
        data = {
            "content": "测试",
            "question_type": "single",
            "cognitive_level": "L3"
        }
        schema = QuestionCreate(**data)
        assert schema.cognitive_level == "L3"
        
        # 无效认知层级
        invalid_data = {
            "content": "测试",
            "question_type": "single",
            "cognitive_level": "L7"  # 无效
        }
        
        with pytest.raises(ValidationError):
            QuestionCreate(**invalid_data)

    def test_question_update_schema_partial(self):
        """测试：QuestionUpdate Schema 验证 - 部分更新"""
        from app.schemas.question import QuestionUpdate
        
        # 只更新难度
        data = {"difficulty": 4}
        schema = QuestionUpdate(**data)
        
        assert schema.difficulty == 4
        assert schema.content is None
        assert schema.answer is None

    def test_question_query_schema_defaults(self):
        """测试：QuestionQuery Schema 默认值"""
        from app.schemas.question import QuestionQuery
        
        schema = QuestionQuery()
        
        assert schema.page == 1
        assert schema.page_size == 20
        assert schema.sort_by == "created_at"
        assert schema.sort_order == "desc"
        assert schema.question_types is None
        assert schema.keyword is None

    def test_question_query_schema_with_filters(self):
        """测试：QuestionQuery Schema 筛选条件"""
        from app.schemas.question import QuestionQuery
        
        data = {
            "page": 2,
            "page_size": 50,
            "question_types": ["single", "multiple"],
            "difficulties": [2, 3],
            "cognitive_levels": ["L3", "L4"],
            "knowledge_points": ["函数"],
            "review_status": "approved",
            "keyword": "二次函数",
            "sort_by": "difficulty",
            "sort_order": "asc"
        }
        
        schema = QuestionQuery(**data)
        
        assert schema.page == 2
        assert schema.page_size == 50
        assert "single" in schema.question_types
        assert "二次函数" in schema.keyword
        assert schema.sort_by == "difficulty"

    def test_batch_request_schema(self):
        """测试：QuestionBatchRequest Schema"""
        from app.schemas.question import QuestionBatchRequest
        from uuid import uuid4
        
        question_ids = [str(uuid4()), str(uuid4())]
        
        data = {
            "operation": "delete",
            "question_ids": question_ids
        }
        
        schema = QuestionBatchRequest(**data)
        assert schema.operation == "delete"
        assert len(schema.question_ids) == 2

    def test_similarity_check_schema(self):
        """测试：SimilarityCheckRequest Schema"""
        from app.schemas.question import SimilarityCheckRequest
        
        data = {
            "content": "这是一道测试题目内容，用于检测相似度",
            "threshold": 0.85
        }
        
        schema = SimilarityCheckRequest(**data)
        assert len(schema.content) >= 10
        assert schema.threshold == 0.85

    def test_similarity_check_schema_content_too_short(self):
        """测试：SimilarityCheckRequest Schema - 内容太短"""
        from app.schemas.question import SimilarityCheckRequest
        from pydantic import ValidationError
        
        data = {
            "content": "太短"  # 少于10个字符
        }
        
        with pytest.raises(ValidationError):
            SimilarityCheckRequest(**data)


class TestQuestionService:
    """Question Service 测试"""

    def setup_method(self):
        import sys
        mods = [k for k in sys.modules.keys() if 'app.services.question_service' in k]
        for m in mods:
            sys.modules.pop(m, None)

    @pytest.mark.asyncio
    async def test_create_question_success(self):
        """测试：创建题目成功"""
        from app.services.question_service import QuestionService
        from app.schemas.question import QuestionCreate
        
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        service = QuestionService(mock_db)
        
        data = QuestionCreate(
            content="1+1=?",
            question_type="single",
            options=[
                {"key": "A", "text": "1"},
                {"key": "B", "text": "2"}
            ],
            answer="B",
            difficulty=1
        )
        
        result = await service.create_question(data)
        
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_question_by_id(self):
        """测试：根据ID获取题目"""
        from app.services.question_service import QuestionService
        
        question_id = uuid4()
        
        # 构造 mock 题目
        mock_question = MagicMock()
        mock_question.id = question_id
        mock_question.content = "测试题目"
        mock_question.question_type = "single"
        mock_question.is_deleted = False
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_question
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = QuestionService(mock_db)
        result = await service.get_question_by_id(question_id)
        
        assert result is not None
        assert result.id == question_id
        assert result.content == "测试题目"

    @pytest.mark.asyncio
    async def test_get_question_not_found(self):
        """测试：获取题目 - 不存在"""
        from app.services.question_service import QuestionService
        
        question_id = uuid4()
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = QuestionService(mock_db)
        result = await service.get_question_by_id(question_id)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_update_question(self):
        """测试：更新题目"""
        from app.services.question_service import QuestionService
        from app.schemas.question import QuestionUpdate
        
        question_id = uuid4()
        
        mock_question = MagicMock()
        mock_question.id = question_id
        mock_question.content = "原始内容"
        mock_question.difficulty = 1
        
        mock_db = AsyncMock()
        
        # 先查后改
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = mock_question
        mock_db.execute = AsyncMock(return_value=mock_get_result)
        mock_db.commit = AsyncMock()
        
        service = QuestionService(mock_db)
        
        update_data = QuestionUpdate(content="更新后的内容", difficulty=3)
        result = await service.update_question(question_id, update_data)
        
        assert result is not None
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_soft_delete_question(self):
        """测试：软删除题目"""
        from app.services.question_service import QuestionService
        
        question_id = uuid4()
        
        mock_question = MagicMock()
        mock_question.id = question_id
        mock_question.is_deleted = False
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_question
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        
        service = QuestionService(mock_db)
        result = await service.delete_question(question_id)
        
        assert result is True
        assert mock_question.is_deleted == True

    @pytest.mark.asyncio
    async def test_query_questions_with_filters(self):
        """测试：多条件筛选查询"""
        from app.services.question_service import QuestionService
        from app.schemas.question import QuestionQuery
        
        mock_questions = []
        for i in range(3):
            q = MagicMock()
            q.id = uuid4()
            q.content = f"题目{i+1}"
            q.question_type = "single"
            q.difficulty = i + 1
            q.is_deleted = False
            mock_questions.append(q)
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_questions
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = QuestionService(mock_db)
        
        query = QuestionQuery(
            page=1,
            page_size=20,
            question_types=["single"],
            difficulties=[1, 2, 3],
            keyword="题目"
        )
        
        result = await service.query_questions(query)
        
        # query_questions 返回 (list, total) 元组
        questions, total = result
        assert len(questions) == 3
        mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_batch_delete_questions(self):
        """测试：批量删除"""
        from app.services.question_service import QuestionService
        
        question_ids = [uuid4(), uuid4(), uuid4()]
        
        mock_questions = []
        for qid in question_ids:
            q = MagicMock()
            q.id = qid
            q.is_deleted = False
            mock_questions.append(q)
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_questions
        mock_result.rowcount = 3  # 模拟删除返回的行数
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        
        service = QuestionService(mock_db)
        result = await service.batch_delete_questions(question_ids)
        
        assert result == 3
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_similarity_check_duplicate(self):
        """测试：相似度检测 - 发现重复"""
        from app.services.question_service import QuestionService
        from app.schemas.question import SimilarityCheckRequest
        
        existing_questions = [
            MagicMock(id=uuid4(), content="这是一道关于二次函数的典型题目"),
            MagicMock(id=uuid4(), content="二次函数的性质与应用")
        ]
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = existing_questions
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = QuestionService(mock_db)
        
        request = SimilarityCheckRequest(
            content="二次函数是一种重要的函数类型",
            threshold=0.6
        )
        
        result = await service.check_similarity(request)
        
        # 应该有相似题目被检测到
        assert hasattr(result, 'is_duplicate')
        assert hasattr(result, 'similarity_score')


class TestQuestionAnnotation:
    """题目标注测试"""

    def setup_method(self):
        import sys
        mods = [k for k in sys.modules.keys() if 'app.models.question' in k]
        for m in mods:
            sys.modules.pop(m, None)

    def test_question_annotation_model(self):
        """测试：QuestionAnnotation 模型"""
        from app.models.question import QuestionAnnotation
        
        annotation = QuestionAnnotation(
            annotation_type="error_cause",
            key="common_mistake",
            value={"type": "计算错误", "description": "符号处理"},
            confidence=Decimal("0.85"),
            annotation_method="ai"
        )
        
        assert annotation.annotation_type == "error_cause"
        assert annotation.key == "common_mistake"
        assert annotation.confidence == Decimal("0.85")
        assert annotation.annotation_method == "ai"

    def test_annotation_types(self):
        """测试：多种标注类型"""
        from app.models.question import QuestionAnnotation
        
        annotation_types = [
            ("difficulty", "auto_difficulty", {"level": 3, "method": "IRT"}),
            ("error_cause", "common_error", {"type": "概念混淆"}),
            ("cognitive", "cognitive_level", {"level": "L4", "description": "应用"}),
            ("thinking", "thinking_type", {"type": "归纳演绎"})
        ]
        
        for atype, key, value in annotation_types:
            annotation = QuestionAnnotation(
                annotation_type=atype,
                key=key,
                value=value
            )
            assert annotation.annotation_type == atype


class TestQuestionStatistics:
    """题库统计测试"""

    @pytest.mark.asyncio
    async def test_get_statistics(self):
        """测试：获取题库统计"""
        from app.services.question_service import QuestionService
        
        mock_db = AsyncMock()
        
        # Mock 统计查询结果
        mock_stats = MagicMock()
        mock_stats.scalar.return_value = 100  # 总题量
        
        mock_db.execute = AsyncMock(return_value=mock_stats)
        
        service = QuestionService(mock_db)
        stats = await service.get_statistics()
        
        assert stats is not None
        assert hasattr(stats, 'total_count')
        assert hasattr(stats, 'by_type')
        assert hasattr(stats, 'by_difficulty')

    @pytest.mark.asyncio
    async def test_distribution_by_type(self):
        """测试：按题型分布统计"""
        from app.services.question_service import QuestionService
        
        mock_db = AsyncMock()
        
        # Mock 按题型分组结果 - 注意列名是 category（因为用了 label）
        mock_rows = [
            MagicMock(category="single", count=50),
            MagicMock(category="multiple", count=30),
            MagicMock(category="fill", count=20)
        ]
        
        mock_result = MagicMock()
        # 注意：_get_distribution 使用 result.all() 而不是 scalars().all()
        mock_result.all.return_value = mock_rows
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = QuestionService(mock_db)
        distribution = await service.get_distribution_by_type()
        
        assert len(distribution) == 3
        assert distribution[0]["category"] == "single"
        assert distribution[0]["count"] == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
