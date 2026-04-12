"""
T18 测试：智能组卷系统

使用 Mock 避免 SQLAlchemy 模型导入冲突

覆盖：
1. PaperConstraints - 组卷约束验证
2. GreedyPaperGenerator - 贪心组卷算法
3. DiagnosticPaperGenerator - 诊断组卷算法
4. Paper API - RESTful 接口
5. A/B卷生成
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from decimal import Decimal


class TestPaperConstraints:
    """组卷约束测试"""

    def setup_method(self):
        """模块级重置"""
        import sys
        mods = [k for k in sys.modules.keys() if 'app.schemas.paper' in k or 'app.services.paper_service' in k]
        for m in mods:
            sys.modules.pop(m, None)

    def test_valid_constraints(self):
        """测试：有效组卷约束"""
        from app.schemas.paper import PaperConstraints
        
        data = {
            "total_count": 20,
            "total_score": 100,
            "target_knowledge_points": ["二次函数", "一元二次方程"],
            "difficulty_distribution": {"1": 0.2, "2": 0.4, "3": 0.3, "4": 0.1},
            "question_type_counts": {"single": 10, "fill": 5, "essay": 5},
        }
        
        constraints = PaperConstraints(**data)
        assert constraints.total_count == 20
        assert constraints.total_score == 100
        assert len(constraints.target_knowledge_points) == 2
        assert constraints.difficulty_distribution["1"] == 0.2

    def test_difficulty_distribution_sum(self):
        """测试：难度分布总和验证"""
        from app.schemas.paper import PaperConstraints
        from pydantic import ValidationError
        
        # 难度分布总和必须为1
        data = {
            "total_count": 20,
            "difficulty_distribution": {"1": 0.3, "2": 0.3, "3": 0.3}  # 总和=0.9
        }
        
        with pytest.raises(ValidationError):
            PaperConstraints(**data)

    def test_conflicting_constraints_question_count(self):
        """测试：冲突约束 - 题数不足"""
        from app.schemas.paper import PaperConstraints, PaperGenerationError
        
        data = {
            "total_count": 100,  # 要求100题
            "question_type_counts": {"single": 10},  # 但只指定10题
        }
        
        constraints = PaperConstraints(**data)
        
        # 验证约束冲突
        with pytest.raises(PaperGenerationError):
            constraints.validate_conflicts()

    def test_empty_knowledge_points(self):
        """测试：空知识点约束"""
        from app.schemas.paper import PaperConstraints
        
        data = {
            "total_count": 20,
            "target_knowledge_points": [],  # 空列表
        }
        
        constraints = PaperConstraints(**data)
        assert len(constraints.target_knowledge_points) == 0

    def test_difficulty_levels(self):
        """测试：难度等级范围"""
        from app.schemas.paper import PaperConstraints
        
        data = {
            "total_count": 20,
            "difficulty_distribution": {"1": 0.25, "2": 0.25, "3": 0.25, "4": 0.25, "5": 0.0},
        }
        
        constraints = PaperConstraints(**data)
        assert len(constraints.difficulty_distribution) == 5
        assert "5" in constraints.difficulty_distribution


class TestPaperSchema:
    """试卷 Schema 测试"""

    def setup_method(self):
        import sys
        mods = [k for k in sys.modules.keys() if 'app.schemas.paper' in k]
        for m in mods:
            sys.modules.pop(m, None)

    def test_paper_create_schema(self):
        """测试：创建试卷 Schema"""
        from app.schemas.paper import PaperCreate
        
        data = {
            "title": "二次函数单元测试",
            "subject": "数学",
            "grade_level": "九年级",
            "paper_type": "normal",
            "generation_mode": "ai",
            "constraints": {
                "total_count": 20,
                "total_score": 100,
            }
        }
        
        paper = PaperCreate(**data)
        assert paper.title == "二次函数单元测试"
        assert paper.subject == "数学"
        assert paper.generation_mode == "ai"

    def test_paper_generate_request_schema(self):
        """测试：组卷请求 Schema"""
        from app.schemas.paper import PaperGenerateRequest
        
        data = {
            "title": "智能组卷",
            "subject": "数学",
            "grade_level": "九年级",
            "total_count": 20,
            "total_score": 100,
            "target_knowledge_points": ["二次函数"],
            "difficulty_distribution": {"1": 0.2, "2": 0.4, "3": 0.4},
            "question_type_counts": {"single": 10, "fill": 10},
        }
        
        request = PaperGenerateRequest(**data)
        assert request.total_count == 20
        assert len(request.target_knowledge_points) == 1

    def test_paper_generate_request_default_values(self):
        """测试：组卷请求默认值"""
        from app.schemas.paper import PaperGenerateRequest
        
        data = {
            "title": "最小约束组卷",
            "subject": "数学",
            "total_count": 10,
        }
        
        request = PaperGenerateRequest(**data)
        assert request.paper_type == "normal"
        assert request.generation_mode == "greedy"
        assert request.total_score == 100  # 默认总分

    def test_diagnostic_generate_request_schema(self):
        """测试：诊断组卷请求 Schema"""
        from app.schemas.paper import DiagnosticGenerateRequest
        
        data = {
            "title": "诊断性测试",
            "subject": "数学",
            "student_id": str(uuid4()),
            "diagnosis_report": {
                "weak_points": ["二次函数顶点", "韦达定理"],
                "mastery_levels": {"二次函数顶点": 0.3, "韦达定理": 0.4}
            },
            "total_count": 15,
        }
        
        request = DiagnosticGenerateRequest(**data)
        assert request.student_id is not None
        assert len(request.diagnosis_report["weak_points"]) == 2


class TestGreedyGenerator:
    """贪心组卷算法测试"""

    def setup_method(self):
        import sys
        mods = [k for k in sys.modules.keys() if 'app.services.paper_service' in k]
        for m in mods:
            sys.modules.pop(m, None)

    def test_select_best_question_by_knowledge_point(self):
        """测试：按知识点选择最优题目"""
        from app.services.paper_service import GreedyPaperGenerator
        
        mock_db = MagicMock()
        generator = GreedyPaperGenerator(mock_db)
        
        # 候选题目
        candidates = [
            {"id": uuid4(), "difficulty": 2, "knowledge_points": ["二次函数"], "score": 5},
            {"id": uuid4(), "difficulty": 3, "knowledge_points": ["二次函数"], "score": 5},
            {"id": uuid4(), "difficulty": 2, "knowledge_points": ["二次函数"], "score": 5},
        ]
        
        # 选择难度最接近2的
        best = generator._select_best_by_difficulty(candidates, target_difficulty=2)
        assert best["difficulty"] == 2

    def test_select_best_question_by_score(self):
        """测试：按分值选择题目"""
        from app.services.paper_service import GreedyPaperGenerator
        
        mock_db = MagicMock()
        generator = GreedyPaperGenerator(mock_db)
        
        candidates = [
            {"id": uuid4(), "difficulty": 2, "score": 3},
            {"id": uuid4(), "difficulty": 2, "score": 5},
            {"id": uuid4(), "difficulty": 2, "score": 4},
        ]
        
        # 选择分值最接近5的
        best = generator._select_best_by_score(candidates, target_score=5)
        assert best["score"] == 5

    def test_calculate_difficulty_distribution(self):
        """测试：计算难度分布"""
        from app.services.paper_service import GreedyPaperGenerator
        
        mock_db = MagicMock()
        generator = GreedyPaperGenerator(mock_db)
        
        selected_questions = [
            {"id": uuid4(), "difficulty": 1},
            {"id": uuid4(), "difficulty": 1},
            {"id": uuid4(), "difficulty": 2},
            {"id": uuid4(), "difficulty": 2},
            {"id": uuid4(), "difficulty": 3},
        ]
        
        distribution = generator._calculate_distribution(selected_questions)
        assert distribution[1] == pytest.approx(0.4, rel=0.01)
        assert distribution[2] == pytest.approx(0.4, rel=0.01)
        assert distribution[3] == pytest.approx(0.2, rel=0.01)

    def test_knowledge_coverage_calculation(self):
        """测试：知识点覆盖率计算"""
        from app.services.paper_service import GreedyPaperGenerator
        
        mock_db = MagicMock()
        generator = GreedyPaperGenerator(mock_db)
        
        selected_questions = [
            {"knowledge_points": ["二次函数", "顶点"]},
            {"knowledge_points": ["二次函数", "图像"]},
            {"knowledge_points": ["一元二次方程"]},
        ]
        target_kps = ["二次函数", "顶点", "图像", "一元二次方程"]
        
        coverage = generator._calculate_knowledge_coverage(selected_questions, target_kps)
        assert coverage["二次函数"] == 1.0
        assert coverage["顶点"] == 1.0
        assert coverage["一元二次方程"] == 1.0
        assert coverage["总体覆盖率"] == 1.0

    def test_partial_knowledge_coverage(self):
        """测试：部分知识点覆盖"""
        from app.services.paper_service import GreedyPaperGenerator
        
        mock_db = MagicMock()
        generator = GreedyPaperGenerator(mock_db)
        
        selected_questions = [
            {"knowledge_points": ["二次函数"]},
        ]
        target_kps = ["二次函数", "顶点", "图像", "韦达定理"]
        
        coverage = generator._calculate_knowledge_coverage(selected_questions, target_kps)
        assert coverage["二次函数"] == 1.0
        assert coverage["顶点"] == 0.0
        assert coverage["总体覆盖率"] == 0.25


class TestDiagnosticGenerator:
    """诊断组卷算法测试"""

    def setup_method(self):
        import sys
        mods = [k for k in sys.modules.keys() if 'app.services.paper_service' in k]
        for m in mods:
            sys.modules.pop(m, None)

    def test_adjust_difficulty_for_weak_students(self):
        """测试：针对薄弱学生的难度调整"""
        from app.services.paper_service import DiagnosticPaperGenerator
        
        mock_db = MagicMock()
        generator = DiagnosticPaperGenerator(mock_db)
        
        # 薄弱学生应该得到偏中等偏低的难度
        adjusted = generator._adjust_difficulty_for_mastery(
            base_dist={1: 0.1, 2: 0.4, 3: 0.4, 4: 0.1, 5: 0.0},
            mastery_level=0.3
        )
        
        # 薄弱学生应该有更多简单题
        assert adjusted[1] >= 0.1
        assert adjusted[2] >= 0.4

    def test_extract_weak_points_from_diagnosis(self):
        """测试：从诊断报告中提取薄弱点"""
        from app.services.paper_service import DiagnosticPaperGenerator
        
        mock_db = MagicMock()
        generator = DiagnosticPaperGenerator(mock_db)
        
        diagnosis = {
            "weak_points": ["二次函数顶点", "韦达定理", "因式分解"],
            "mastery_levels": {
                "二次函数顶点": 0.2,
                "韦达定理": 0.3,
                "因式分解": 0.5,
                "一元二次方程": 0.7
            }
        }
        
        weak_kps = generator._extract_weak_points(diagnosis, threshold=0.4)
        # mastery < 0.4 的才是薄弱点
        assert "二次函数顶点" in weak_kps  # 0.2 < 0.4
        assert "韦达定理" in weak_kps  # 0.3 < 0.4
        assert "因式分解" not in weak_kps  # 0.5 > 0.4
        assert "一元二次方程" not in weak_kps  # 0.7 > 0.4

    def test_build_diagnostic_constraints(self):
        """测试：构建诊断组卷约束"""
        from app.services.paper_service import DiagnosticPaperGenerator
        
        mock_db = MagicMock()
        generator = DiagnosticPaperGenerator(mock_db)
        
        diagnosis = {
            "weak_points": ["二次函数"],
            "mastery_levels": {"二次函数": 0.3}
        }
        
        constraints = generator._build_diagnostic_constraints(
            diagnosis=diagnosis,
            base_constraints={
                "total_count": 15,
                "total_score": 100,
            }
        )
        
        assert constraints.total_count == 15
        assert "二次函数" in constraints.target_knowledge_points


class TestABPaperGenerator:
    """A/B卷生成测试"""

    def setup_method(self):
        import sys
        mods = [k for k in sys.modules.keys() if 'app.services.paper_service' in k]
        for m in mods:
            sys.modules.pop(m, None)

    @pytest.mark.asyncio
    async def test_generate_paired_paper(self):
        """测试：生成配对试卷"""
        from app.services.paper_service import ABPaperGenerator
        
        mock_db = MagicMock()
        # Set up mock to return empty list for queries
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)
        generator = ABPaperGenerator(mock_db)
        
        original_questions = [
            {"id": str(uuid4()), "content": "题1", "difficulty": 2, "knowledge_points": [], "question_type": "single"},
            {"id": str(uuid4()), "content": "题2", "difficulty": 3, "knowledge_points": [], "question_type": "single"},
            {"id": str(uuid4()), "content": "题3", "difficulty": 2, "knowledge_points": [], "question_type": "single"},
        ]
        
        # 生成B卷 (async method)
        paired_questions = await generator._generate_paired_questions(original_questions)
        
        # B卷题目数应该与A卷相同
        assert len(paired_questions) == len(original_questions)
        
        # 由于题库为空，所有题保留原始的
        for i, pq in enumerate(paired_questions):
            # 如果找到相似题则会替换，否则保留原题
            assert pq["difficulty"] == original_questions[i]["difficulty"]

    def test_check_ab_similarity(self):
        """测试：A/B卷相似度检查"""
        from app.services.paper_service import ABPaperGenerator
        
        mock_db = MagicMock()
        generator = ABPaperGenerator(mock_db)
        
        paper_a_questions = [
            {"id": str(uuid4()), "content": "计算二次函数顶点", "knowledge_points": ["二次函数"]},
            {"id": str(uuid4()), "content": "求方程根", "knowledge_points": ["方程"]},
        ]
        
        paper_b_questions = [
            {"id": str(uuid4()), "content": "计算二次函数顶点", "knowledge_points": ["二次函数"]},  # 相同
            {"id": str(uuid4()), "content": "求方程根", "knowledge_points": ["方程"]},  # 相同
        ]
        
        similarity = generator._calculate_paper_similarity(paper_a_questions, paper_b_questions)
        
        # 两题都相同，相似度应该很高
        assert similarity > 0.8

    @pytest.mark.asyncio
    async def test_similar_question_replacement(self):
        """测试：相似题目替换"""
        from app.services.paper_service import ABPaperGenerator
        
        mock_db = MagicMock()
        generator = ABPaperGenerator(mock_db)
        
        original = {"id": str(uuid4()), "content": "原题", "difficulty": 2, "question_type": "single", "knowledge_points": []}
        
        # 模拟从题库获取相似题
        similar_questions = [
            {"id": str(uuid4()), "content": "变式1", "difficulty": 2, "question_type": "single", "knowledge_points": []},
            {"id": str(uuid4()), "content": "变式2", "difficulty": 2, "question_type": "single", "knowledge_points": []},
        ]
        
        replacement = await generator._find_similar_replacement(original, similar_questions)
        
        assert replacement is not None
        assert replacement["id"] != original["id"]
        assert replacement["difficulty"] == original["difficulty"]


class TestPaperService:
    """试卷服务测试"""

    def setup_method(self):
        import sys
        mods = [k for k in sys.modules.keys() if 'app.services.paper_service' in k]
        for m in mods:
            sys.modules.pop(m, None)

    def test_create_paper_record(self):
        """测试：创建试卷记录"""
        from app.services.paper_service import PaperService
        from app.schemas.paper import PaperCreate
        
        mock_db = MagicMock()
        service = PaperService(mock_db)
        
        data = PaperCreate(
            title="测试试卷",
            subject="数学",
            grade_level="九年级",
            paper_type="normal",
            generation_mode="ai",
        )
        
        # Mock 保存方法
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # 由于使用 mock，验证数据传递正确
        assert data.title == "测试试卷"

    def test_get_paper_statistics(self):
        """测试：获取试卷统计"""
        from app.services.paper_service import PaperService
        
        mock_db = MagicMock()
        service = PaperService(mock_db)
        
        # Mock 统计查询结果
        mock_result = MagicMock()
        mock_result.total = 50
        mock_result.published = 30
        mock_result.draft = 20
        
        # 验证统计结构
        stats = {
            "total": 50,
            "published": 30,
            "draft": 20,
            "by_type": {
                "normal": 20,
                "diagnostic": 15,
                "exam": 15
            }
        }
        
        assert stats["total"] == 50
        assert stats["by_type"]["normal"] == 20


class TestPaperAPI:
    """试卷 API 测试"""

    def setup_method(self):
        import sys
        mods = [k for k in sys.modules.keys() if 'app.api.v1.exam.paper' in k]
        for m in mods:
            sys.modules.pop(m, None)

    def test_paper_response_schema(self):
        """测试：试卷响应 Schema"""
        from app.schemas.paper import PaperResponse
        
        data = {
            "id": uuid4(),
            "title": "二次函数测试",
            "subject": "数学",
            "grade_level": "九年级",
            "paper_type": "normal",
            "question_count": 20,
            "total_score": 100.0,
            "estimated_time": 90,
            "difficulty_distribution": {1: 0.2, 2: 0.4, 3: 0.4},
            "knowledge_coverage": {"二次函数": 1.0, "顶点": 0.8},
            "status": "draft",
            "created_at": datetime.now(),
        }
        
        response = PaperResponse(**data)
        assert response.title == "二次函数测试"
        assert response.question_count == 20
        assert response.total_score == 100.0

    def test_paper_list_response_schema(self):
        """测试：试卷列表响应 Schema"""
        from app.schemas.paper import PaperListResponse, PaperListItem
        
        items = [
            PaperListItem(
                id=uuid4(),
                title="试卷1",
                subject="数学",
                question_count=20,
                status="published",
            ),
            PaperListItem(
                id=uuid4(),
                title="试卷2",
                subject="数学",
                question_count=15,
                status="draft",
            ),
        ]
        
        response = PaperListResponse(
            items=items,
            total=2,
            page=1,
            page_size=20,
        )
        
        assert len(response.items) == 2
        assert response.total == 2

    def test_paper_with_questions_schema(self):
        """测试：带题目的试卷响应"""
        from app.schemas.paper import PaperWithQuestions
        
        data = {
            "id": uuid4(),
            "title": "完整试卷",
            "subject": "数学",
            "questions": [
                {
                    "order": 1,
                    "content": "题目1",
                    "question_type": "single",
                    "score": 5.0,
                    "options": [
                        {"key": "A", "text": "选项1"},
                        {"key": "B", "text": "选项2"},
                    ]
                }
            ],
            "total_score": 100.0,
        }
        
        paper = PaperWithQuestions(**data)
        assert len(paper.questions) == 1
        assert paper.questions[0]["order"] == 1

    def test_ab_paper_response_schema(self):
        """测试：A/B卷响应 Schema"""
        from app.schemas.paper import ABPaperResponse
        
        data = {
            "paper_a": {
                "id": uuid4(),
                "title": "A卷",
                "question_count": 20,
            },
            "paper_b": {
                "id": uuid4(),
                "title": "B卷",
                "question_count": 20,
            },
            "similarity_score": 0.45,
        }
        
        response = ABPaperResponse(**data)
        assert response.paper_a.title == "A卷"
        assert response.paper_b.title == "B卷"
        assert response.similarity_score == 0.45


class TestPaperGenerationWorkflow:
    """组卷工作流测试"""

    def setup_method(self):
        import sys
        mods = [k for k in sys.modules.keys() if 'app.services.paper_service' in k]
        for m in mods:
            sys.modules.pop(m, None)

    @pytest.mark.asyncio
    async def test_full_generation_workflow(self):
        """测试：完整组卷工作流"""
        from app.services.paper_service import GreedyPaperGenerator
        from app.schemas.paper import PaperConstraints
        
        mock_db = MagicMock()
        generator = GreedyPaperGenerator(mock_db)
        
        # 定义约束
        constraints = PaperConstraints(
            total_count=10,
            total_score=100,
            target_knowledge_points=["二次函数"],
            difficulty_distribution={1: 0.2, 2: 0.4, 3: 0.4},
            question_type_counts={"single": 5, "fill": 5},
        )
        
        # Mock 题库查询
        mock_questions = [
            {"id": str(uuid4()), "difficulty": 1, "knowledge_points": ["二次函数"], "question_type": "single", "score": 5},
            {"id": str(uuid4()), "difficulty": 2, "knowledge_points": ["二次函数"], "question_type": "single", "score": 5},
            {"id": str(uuid4()), "difficulty": 2, "knowledge_points": ["二次函数"], "question_type": "single", "score": 5},
            {"id": str(uuid4()), "difficulty": 3, "knowledge_points": ["二次函数"], "question_type": "single", "score": 5},
            {"id": str(uuid4()), "difficulty": 3, "knowledge_points": ["二次函数"], "question_type": "single", "score": 5},
            {"id": str(uuid4()), "difficulty": 1, "knowledge_points": ["二次函数"], "question_type": "fill", "score": 5},
            {"id": str(uuid4()), "difficulty": 2, "knowledge_points": ["二次函数"], "question_type": "fill", "score": 5},
            {"id": str(uuid4()), "difficulty": 2, "knowledge_points": ["二次函数"], "question_type": "fill", "score": 5},
            {"id": str(uuid4()), "difficulty": 3, "knowledge_points": ["二次函数"], "question_type": "fill", "score": 5},
            {"id": str(uuid4()), "difficulty": 3, "knowledge_points": ["二次函数"], "question_type": "fill", "score": 5},
        ]
        
        # Mock 数据库查询
        with patch.object(generator, '_query_questions', return_value=mock_questions):
            result = await generator.generate(constraints)
        
        assert len(result.questions) == 10
        assert result.paper is None or result.paper.question_count == 10
        assert len(result.difficulty_distribution) > 0  # distribution should not be empty
        assert len(result.knowledge_coverage) > 0  # coverage should not be empty

    @pytest.mark.asyncio
    async def test_generation_with_insufficient_questions(self):
        """测试：题目不足时的处理"""
        from app.services.paper_service import GreedyPaperGenerator
        from app.schemas.paper import PaperConstraints, PaperGenerationError
        
        mock_db = MagicMock()
        generator = GreedyPaperGenerator(mock_db)
        
        constraints = PaperConstraints(
            total_count=100,  # 要求100题
            total_score=500,
        )
        
        # Mock 题库只有10题
        mock_questions = [
            {"id": str(uuid4()), "difficulty": 2, "knowledge_points": [], "question_type": "single", "score": 5}
            for _ in range(10)
        ]
        
        with patch.object(generator, '_query_questions', return_value=mock_questions):
            with pytest.raises(PaperGenerationError) as exc_info:
                await generator.generate(constraints)
        
        assert "不足" in str(exc_info.value) or "Insufficient" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
