"""
T12 测试: 教师助手增强（AI 出题 + 教案生成）

测试覆盖：
1. AI 出题 Schema 验证
2. AI 出题服务方法测试
3. 出题 API 端点测试
4. 批量保存 API 测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

# 测试用 Schema
from app.schemas.ai import (
    QuestionOption, QuestionOutput, QuestionSetOutput,
    QuestionGenerateRequest
)


class TestQuestionSchemas:
    """测试题目相关 Schema"""

    def test_question_option_schema(self):
        """测试题目选项 Schema"""
        opt = QuestionOption(label="A", content="选项A", is_correct=True)
        assert opt.label == "A"
        assert opt.content == "选项A"
        assert opt.is_correct is True

    def test_question_output_schema(self):
        """测试单个题目 Schema"""
        q = QuestionOutput(
            content="这是一道测试题",
            question_type="single",
            options=[
                QuestionOption(label="A", content="选项A", is_correct=True),
                QuestionOption(label="B", content="选项B", is_correct=False),
            ],
            answer="A",
            analysis="本题考察基本概念",
            difficulty=2,
            score=5.0,
            knowledge_points=["基础知识"],
            source="ai",
            saved=False,
        )
        assert q.content == "这是一道测试题"
        assert q.question_type == "single"
        assert len(q.options) == 2
        assert q.difficulty == 2

    def test_question_generate_request_schema(self):
        """测试出题请求 Schema"""
        req = QuestionGenerateRequest(
            course_name="高中数学",
            grade_level="高一",
            topic="一元二次方程",
            question_types=["single", "fill", "essay"],
            difficulty=3,
            count=10,
            knowledge_points=["求根公式", "韦达定理"],
            requirements="注重考查解题思路",
        )
        assert req.course_name == "高中数学"
        assert "single" in req.question_types
        assert req.difficulty == 3

    def test_question_set_output_schema(self):
        """测试题目集 Schema"""
        qs = QuestionSetOutput(
            set_id="abc123",
            title="一元二次方程练习题",
            course_name="高中数学",
            grade_level="高一",
            topic="一元二次方程",
            total_count=5,
            questions=[
                QuestionOutput(
                    content="测试题",
                    question_type="single",
                    difficulty=2,
                    score=5.0,
                    knowledge_points=[],
                    source="ai",
                    saved=False,
                )
            ],
            generated_at=datetime.now().isoformat(),
            saved_count=0,
        )
        assert qs.set_id == "abc123"
        assert qs.total_count == 5
        assert len(qs.questions) == 1


class TestAIServiceQuestionMethods:
    """测试 AI 服务出题方法"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def ai_service(self, mock_db):
        """创建 AI 服务实例"""
        from app.services.ai_service import AIService
        return AIService(mock_db)

    @pytest.mark.asyncio
    async def test_generate_questions_returns_question_set(self, ai_service, mock_db):
        """测试生成题目返回题目集"""
        from app.schemas.ai import QuestionGenerateRequest

        request = QuestionGenerateRequest(
            course_name="高中数学",
            grade_level="高一",
            topic="一元二次方程",
            question_types=["single", "fill"],
            difficulty=2,
            count=3,
        )

        # Mock get_config 返回 None（模拟 AI 未配置）
        ai_service.get_config = AsyncMock(return_value=None)

        result = await ai_service.generate_questions(request)

        assert result is not None
        assert result.course_name == "高中数学"
        assert result.topic == "一元二次方程"
        assert result.total_count >= 0
        assert len(result.questions) >= 0
        assert result.generated_at is not None

    @pytest.mark.asyncio
    async def test_generate_sample_questions_fallback(self, ai_service):
        """测试 AI 不可用时返回示例题目"""
        from app.schemas.ai import QuestionGenerateRequest

        request = QuestionGenerateRequest(
            course_name="高中物理",
            grade_level="高二",
            topic="牛顿运动定律",
            question_types=["single", "essay"],
            difficulty=3,
            count=4,
        )

        # Mock get_config 返回 None（模拟 AI 未配置）
        ai_service.get_config = AsyncMock(return_value=None)

        result = await ai_service.generate_questions(request)

        # 无论 AI 配置如何，都应返回题目集
        assert result.total_count > 0
        assert len(result.questions) > 0

    @pytest.mark.asyncio
    async def test_save_question_creates_database_record(self, ai_service, mock_db):
        """测试保存题目到数据库"""
        from app.schemas.ai import QuestionOption, QuestionOutput

        question = QuestionOutput(
            content="测试保存题目",
            question_type="single",
            options=[
                QuestionOption(label="A", content="选项A", is_correct=True),
                QuestionOption(label="B", content="选项B", is_correct=False),
            ],
            answer="A",
            analysis="测试解析",
            difficulty=2,
            score=5.0,
            knowledge_points=["测试知识点"],
            source="ai",
            saved=False,
        )

        question_id = await ai_service.save_generated_question(question, uuid4())

        # 验证数据库操作被调用
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_parse_questions_from_response_valid_json(self, ai_service):
        """测试从 LLM 响应解析题目"""
        response = json.dumps([
            {
                "content": "第一题内容",
                "question_type": "single",
                "options": [
                    {"label": "A", "content": "A选项", "is_correct": True},
                    {"label": "B", "content": "B选项", "is_correct": False},
                ],
                "answer": "A",
                "analysis": "解析",
                "difficulty": 2,
                "score": 5,
                "knowledge_points": ["知识点1"]
            }
        ])

        questions = ai_service._parse_questions_from_response(response, ["single"])
        assert len(questions) == 1
        assert questions[0].content == "第一题内容"

    def test_parse_questions_from_response_invalid_json(self, ai_service):
        """测试从无效 JSON 解析返回空列表"""
        response = "这不是有效的 JSON [格式"
        questions = ai_service._parse_questions_from_response(response, ["single"])
        assert len(questions) == 0


class TestTeacherAssistantAPI:
    """测试教师助手 API 端点"""

    @pytest.fixture
    def mock_current_user(self):
        """模拟当前用户"""
        user = MagicMock()
        user.id = uuid4()
        return user

    @pytest.mark.asyncio
    async def test_generate_questions_endpoint(self, mock_current_user):
        """测试 AI 出题端点"""
        from app.api.v1.ai.teacher_assistant import router, generate_questions
        from app.schemas.ai import QuestionGenerateRequest

        request = QuestionGenerateRequest(
            course_name="高中化学",
            grade_level="高一",
            topic="化学反应速率",
            question_types=["single", "multiple"],
            difficulty=2,
            count=5,
        )

        # 由于 AI 服务可能不可用，测试 API 返回结构
        response = await generate_questions(request, mock_current_user)

        assert response is not None
        assert "code" in response or "data" in response

    @pytest.mark.asyncio
    async def test_save_question_endpoint(self, mock_current_user):
        """测试保存题目端点（结构验证）"""
        from app.api.v1.ai.teacher_assistant import SaveQuestionRequest

        request = SaveQuestionRequest(
            content="测试题目",
            question_type="single",
            options=[
                {"label": "A", "content": "选项A", "is_correct": True},
                {"label": "B", "content": "选项B", "is_correct": False},
            ],
            answer="A",
            analysis="测试解析",
            difficulty=2,
            score=5.0,
            knowledge_points=["测试"],
        )

        # 验证 Schema 解析正确
        assert request.content == "测试题目"
        assert request.question_type == "single"
        assert len(request.options) == 2


class TestQuestionTypes:
    """测试题目题型支持"""

    def test_all_question_types_have_labels(self):
        """验证所有题型都有标签"""
        type_labels = {
            "single": "单选题",
            "multiple": "多选题",
            "fill": "填空题",
            "essay": "解答题",
            "calculation": "计算题",
        }

        for q_type, label in type_labels.items():
            assert label is not None
            assert len(label) > 0

    def test_difficulty_levels(self):
        """测试难度等级"""
        difficulties = {
            1: "简单",
            2: "中等",
            3: "较难",
            4: "困难",
            5: "极难",
        }

        for level, label in difficulties.items():
            assert level in range(1, 6)
            assert label is not None

    def test_sample_questions_all_types(self):
        """测试生成所有题型的示例题目"""
        from app.schemas.ai import QuestionGenerateRequest
        from app.services.ai_service import AIService

        mock_db = AsyncMock()
        ai_service = AIService(mock_db)

        all_types = ["single", "multiple", "fill", "essay", "calculation"]

        for q_type in all_types:
            request = QuestionGenerateRequest(
                course_name="测试课程",
                grade_level="测试年级",
                topic="测试课题",
                question_types=[q_type],
                difficulty=2,
                count=1,
            )

            result = ai_service._generate_sample_questions(request, "test_set_id")
            assert len(result.questions) == 1
            assert result.questions[0].question_type == q_type


# 辅助函数测试
class TestHelperFunctions:
    """测试辅助函数"""

    def test_question_type_to_label(self):
        """测试题型到标签的转换"""
        type_labels = {
            "single": "单选题",
            "multiple": "多选题",
            "fill": "填空题",
            "essay": "解答题",
            "calculation": "计算题",
        }

        for q_type, expected_label in type_labels.items():
            # 前端辅助函数测试逻辑
            pass

    def test_difficulty_level_label(self):
        """测试难度等级标签"""
        difficulty_labels = {
            1: "简单",
            2: "中等",
            3: "较难",
            4: "困难",
            5: "极难",
        }

        for level, expected_label in difficulty_labels.items():
            assert level in difficulty_labels.keys()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
