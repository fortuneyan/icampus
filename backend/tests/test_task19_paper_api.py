"""
T19 智能组卷 API 路由 - 测试用例
Test-Driven Development: Red-Green-Refactor 循环

运行方式: pytest tests/test_task19_paper_api.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
from httpx import AsyncClient, ASGITransport

# =============================================================================
# 测试夹具 (Fixtures)
# =============================================================================

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def mock_paper():
    """模拟试卷对象"""
    paper = MagicMock()
    paper.id = uuid4()
    paper.title = "测试试卷"
    paper.subject = "数学"
    paper.grade_level = "高一"
    paper.paper_type = "exam"
    paper.generation_mode = "greedy"
    paper.constraints = {"total_count": 20, "difficulty_distribution": {"1": 0.2, "2": 0.4}}
    paper.question_ids = [str(uuid4()) for _ in range(20)]
    paper.question_count = 20
    paper.total_score = 100.0
    paper.status = "draft"
    paper.is_deleted = False
    paper.created_at = datetime.now()
    paper.updated_at = datetime.now()
    return paper


@pytest.fixture
def valid_generate_request():
    """有效的组卷请求数据"""
    return {
        "title": "高一数学月考试卷",
        "subject": "数学",
        "grade_level": "高一",
        "paper_type": "exam",
        "total_count": 20,
        "total_score": 100,
        "estimated_time": 120,
        "target_knowledge_points": ["二次函数", "一元二次方程"],
        "difficulty_distribution": {"1": 0.2, "2": 0.4, "3": 0.3, "4": 0.1},
        "question_type_counts": {"single": 10, "fill": 10},
    }


@pytest.fixture
def valid_diagnostic_request():
    """有效的诊断组卷请求"""
    return {
        "title": "学生诊断测试",
        "student_id": str(uuid4()),
        "diagnosis_report": {
            "weak_points": ["二次函数顶点", "韦达定理"],
            "mastery_levels": {"二次函数顶点": 0.2, "韦达定理": 0.3}
        },
        "total_count": 15,
        "total_score": 100,
    }


@pytest.fixture
def valid_ab_request():
    """有效的A/B卷请求"""
    return {
        "paper_id": str(uuid4()),  # 原卷 ID
        "title_b": "试卷B",
        "max_similarity": 0.6,
    }


# =============================================================================
# Test Class 1: 组卷请求 Schema 验证
# =============================================================================

class TestGenerateRequestSchema:
    """组卷请求 Schema 验证"""

    def test_valid_request_passes_validation(self, valid_generate_request):
        """有效的组卷请求应该通过验证"""
        from app.schemas.paper import PaperGenerateRequest
        
        request = PaperGenerateRequest(**valid_generate_request)
        
        assert request.title == "高一数学月考试卷"
        assert request.total_count == 20
        assert request.total_score == 100
        assert "二次函数" in request.target_knowledge_points

    def test_missing_required_field_fails(self):
        """缺少必填字段应该失败"""
        from pydantic import ValidationError
        from app.schemas.paper import PaperGenerateRequest
        
        with pytest.raises(ValidationError) as exc_info:
            PaperGenerateRequest(
                subject="数学",
                # 缺少 title, total_count 等必填字段
            )
        
        errors = exc_info.value.errors()
        assert any("title" in str(e) for e in errors)
        assert any("total_count" in str(e) for e in errors)

    def test_invalid_difficulty_distribution_fails(self):
        """无效的难度分布应该失败"""
        from pydantic import ValidationError
        from app.schemas.paper import PaperGenerateRequest
        
        with pytest.raises(ValidationError) as exc_info:
            PaperGenerateRequest(
                title="测试",
                total_count=20,
                difficulty_distribution={"1": 0.2, "2": 2.0}  # 总和超过1
            )
        
        errors = exc_info.value.errors()
        assert any("difficulty_distribution" in str(e).lower() for e in errors)

    def test_negative_count_fails(self):
        """负数题数应该失败"""
        from pydantic import ValidationError
        from app.schemas.paper import PaperGenerateRequest
        
        with pytest.raises(ValidationError):
            PaperGenerateRequest(
                title="测试",
                total_count=-5,  # 负数
            )

    def test_question_type_conflict_detected(self, valid_generate_request):
        """题型数量与总数冲突应该被检测"""
        from app.schemas.paper import PaperGenerateRequest
        
        # 题型总和 > 总数
        valid_generate_request["total_count"] = 10
        valid_generate_request["question_type_counts"] = {"single": 8, "fill": 8}
        
        request = PaperGenerateRequest(**valid_generate_request)
        
        # 应该产生警告
        warnings = request.validate_conflicts()
        assert len(warnings) > 0
        assert any("conflict" in w.lower() for w in warnings)


# =============================================================================
# Test Class 2: 组卷约束验证
# =============================================================================

class TestPaperConstraints:
    """组卷约束验证测试"""

    def test_difficulty_distribution_sum_must_be_one(self):
        """难度分布总和必须为1"""
        from app.schemas.paper import PaperConstraints
        from app.schemas.paper import PaperGenerationError
        
        with pytest.raises(PaperGenerationError):
            PaperConstraints(
                total_count=20,
                difficulty_distribution={"1": 0.2, "2": 0.8, "3": 0.5}  # 总和=1.5
            )

    def test_type_counts_sum_mismatch(self):
        """题型数量与总数不匹配"""
        from app.schemas.paper import PaperConstraints
        from app.schemas.paper import PaperGenerationError
        
        with pytest.raises(PaperGenerationError):
            PaperConstraints(
                total_count=10,
                question_type_counts={"single": 8, "fill": 8}  # 总和=16 > 10
            )

    def test_empty_knowledge_points_allowed(self):
        """空知识点应该允许"""
        from app.schemas.paper import PaperConstraints
        
        constraints = PaperConstraints(
            total_count=20,
            target_knowledge_points=[],
        )
        
        assert constraints.target_knowledge_points == []

    def test_valid_constraints_no_errors(self):
        """有效约束应该无错误"""
        from app.schemas.paper import PaperConstraints
        
        constraints = PaperConstraints(
            total_count=20,
            difficulty_distribution={"1": 0.2, "2": 0.4, "3": 0.3, "4": 0.1},
            question_type_counts={"single": 10, "fill": 10},
            target_knowledge_points=["二次函数"],
        )
        
        assert constraints.total_count == 20
        assert len(constraints.difficulty_distribution) == 4


# =============================================================================
# Test Class 3: 组卷服务层测试
# =============================================================================

class TestPaperService:
    """组卷服务测试"""

    @pytest.mark.asyncio
    async def test_generate_paper_success(self, mock_db, valid_generate_request):
        """成功生成试卷"""
        from app.services.paper_service import GreedyPaperGenerator
        from app.schemas.paper import PaperConstraints
        
        # Mock 查询结果
        mock_questions = [
            MagicMock(
                id=uuid4(),
                content="测试题目",
                question_type="single",
                options=["A", "B", "C", "D"],
                answer="A",
                analysis="解析",
                difficulty=2,
                cognitive_level="L3",
                knowledge_points=["二次函数"],
                score=5.0,
                is_deleted=False,
                review_status="approved",
                has_answer=True,
                usage_count=0,
            )
            for _ in range(25)
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_questions
        mock_db.execute.return_value = mock_result
        
        generator = GreedyPaperGenerator(mock_db)
        constraints = PaperConstraints(
            total_count=20,
            difficulty_distribution={"1": 0.2, "2": 0.4, "3": 0.3, "4": 0.1},
            target_knowledge_points=["二次函数"],
        )
        
        result = await generator.generate(constraints)
        
        assert result is not None
        assert len(result.questions) <= 25
        assert result.difficulty_distribution is not None

    @pytest.mark.asyncio
    async def test_generate_insufficient_questions(self, mock_db):
        """题库不足时抛出错误"""
        from app.services.paper_service import GreedyPaperGenerator
        from app.schemas.paper import PaperConstraints, PaperGenerationError
        
        # Mock 查询返回不足的题目
        mock_questions = [MagicMock() for _ in range(5)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_questions
        mock_db.execute.return_value = mock_result
        
        generator = GreedyPaperGenerator(mock_db)
        constraints = PaperConstraints(
            total_count=20,  # 需要20道题
            difficulty_distribution={"1": 0.2, "2": 0.4, "3": 0.3, "4": 0.1},
        )
        
        with pytest.raises(PaperGenerationError) as exc_info:
            await generator.generate(constraints)
        
        assert "insufficient" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_generate_constraint_conflict(self, mock_db):
        """约束冲突时在构造阶段抛出错误"""
        from app.schemas.paper import PaperConstraints, PaperGenerationError
        
        # 构造约束时应该抛出异常（严格验证模式）
        with pytest.raises(PaperGenerationError):
            PaperConstraints(
                total_count=10,
                question_type_counts={"single": 8, "fill": 8},  # 总和=16 > 10
            )


# =============================================================================
# Test Class 4: 诊断组卷测试
# =============================================================================

class TestDiagnosticPaperGeneration:
    """诊断组卷功能测试"""

    @pytest.mark.asyncio
    async def test_diagnostic_generation_weak_student(self, mock_db, valid_diagnostic_request):
        """薄弱学生的诊断组卷"""
        from app.services.paper_service import DiagnosticPaperGenerator
        from app.schemas.paper import PaperConstraints, DiagnosticGenerateRequest
        
        # Mock 查询结果
        mock_questions = [
            MagicMock(
                id=uuid4(), content="题", question_type="single",
                options=[], answer="A", analysis="", difficulty=1,
                cognitive_level="L2", knowledge_points=["二次函数顶点"],
                score=5.0, is_deleted=False, review_status="approved",
                has_answer=True, usage_count=0,
            )
            for _ in range(20)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_questions
        mock_db.execute.return_value = mock_result
        
        generator = DiagnosticPaperGenerator(mock_db)
        request = DiagnosticGenerateRequest(**valid_diagnostic_request)
        constraints = PaperConstraints(total_count=15)
        
        result = await generator.generate_from_diagnosis(request, constraints)
        
        # 薄弱学生应该生成更多简单题
        assert result is not None

    @pytest.mark.asyncio
    async def test_difficulty_adjustment_for_mastery(self, mock_db):
        """根据掌握度调整难度"""
        from app.services.paper_service import DiagnosticPaperGenerator
        
        generator = DiagnosticPaperGenerator(mock_db)
        
        # 掌握度 < 0.4 -> 偏简单
        dist_low = generator._adjust_difficulty_for_mastery(
            base_dist={"1": 0.1, "2": 0.4, "3": 0.4, "4": 0.1},
            mastery_level=0.3
        )
        assert dist_low.get(1, 0) > 0.15  # 简单题比例更高

    def test_extract_weak_points(self, mock_db):
        """提取薄弱知识点"""
        from app.services.paper_service import DiagnosticPaperGenerator
        
        generator = DiagnosticPaperGenerator(mock_db)
        diagnosis = {
            "mastery_levels": {
                "二次函数": 0.2,  # 薄弱
                "韦达定理": 0.3,  # 薄弱
                "因式分解": 0.8,  # 良好
            }
        }
        
        weak_points = generator._extract_weak_points(diagnosis, threshold=0.4)
        
        assert "二次函数" in weak_points
        assert "韦达定理" in weak_points
        assert "因式分解" not in weak_points


# =============================================================================
# Test Class 5: A/B卷生成测试
# =============================================================================

class TestABPaperGeneration:
    """A/B卷生成功能测试"""

    @pytest.mark.asyncio
    async def test_generate_ab_papers(self, mock_db, mock_paper, valid_ab_request):
        """生成A/B卷"""
        from app.services.paper_service import ABPaperGenerator
        from app.schemas.paper import ABPaperRequest
        
        # Mock 原卷题目
        mock_paper.question_ids = [str(uuid4()) for _ in range(10)]
        
        mock_questions = [
            MagicMock(
                id=uuid4(), content="题", question_type="single",
                difficulty=2, knowledge_points=["函数"],
                is_deleted=False, review_status="approved",
            )
            for _ in range(10)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_questions
        mock_db.execute.return_value = mock_result
        
        generator = ABPaperGenerator(mock_db)
        request = ABPaperRequest(**valid_ab_request)
        
        paper_b, similarity = await generator.generate_paired_paper(mock_paper, request)
        
        assert paper_b is not None
        assert 0 <= similarity <= 1

    def test_calculate_paper_similarity(self, mock_db):
        """计算试卷相似度"""
        from app.services.paper_service import ABPaperGenerator
        
        generator = ABPaperGenerator(mock_db)
        
        questions_a = [
            {"id": "1", "knowledge_points": ["函数", "方程"]},
            {"id": "2", "knowledge_points": ["函数"]},
        ]
        questions_b = [
            {"id": "3", "knowledge_points": ["函数", "方程"]},
            {"id": "4", "knowledge_points": ["函数"]},
        ]
        
        similarity = generator._calculate_paper_similarity(questions_a, questions_b)
        
        assert 0 <= similarity <= 1
        # 相同的知识点多，相似度应该高
        assert similarity > 0.5


# =============================================================================
# Test Class 6: API 响应格式测试
# =============================================================================

class TestAPIResponseFormat:
    """API响应格式测试"""

    def test_error_response_format(self):
        """错误响应格式"""
        from app.schemas.paper import PaperGenerationError
        
        error = PaperGenerationError("测试错误")
        
        assert hasattr(error, "code")
        assert hasattr(error, "message")
        assert error.code == "PAPER_GENERATION_ERROR"

    def test_success_response_format(self, valid_generate_request):
        """成功响应格式"""
        from app.schemas.paper import PaperGenerationResult
        
        result = PaperGenerationResult(
            paper=None,
            questions=[
                {"id": "1", "content": "测试", "difficulty": 2}
            ],
            difficulty_distribution={"1": 0.2, "2": 0.5, "3": 0.3},
            knowledge_coverage={"总体覆盖率": 1.0},
            warnings=[],
        )
        
        assert result.questions is not None
        assert result.difficulty_distribution is not None
        assert len(result.warnings) == 0

    def test_warning_response(self):
        """警告响应"""
        from app.schemas.paper import PaperGenerationResult
        
        result = PaperGenerationResult(
            paper=None,
            questions=[],
            difficulty_distribution={"1": 0.1, "2": 0.2, "3": 0.3},
            knowledge_coverage={"总体覆盖率": 0.8},
            warnings=["知识点覆盖率不足", "难度分布偏差较大"],
        )
        
        assert len(result.warnings) > 0
        assert "覆盖率" in result.warnings[0]


# =============================================================================
# Test Class 7: 试卷管理服务测试
# =============================================================================

class TestPaperManagementService:
    """试卷管理服务测试"""

    @pytest.mark.asyncio
    async def test_list_papers(self, mock_db, mock_paper):
        """列表查询"""
        from app.services.paper_service import PaperService
        
        # Mock 列表查询结果
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = [mock_paper]
        
        # Mock 计数查询结果
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1
        
        # 根据查询参数类型返回不同结果
        async def mock_execute(query):
            if hasattr(query, 'subquery'):
                return mock_count_result
            return mock_list_result
        
        mock_db.execute = mock_execute
        
        service = PaperService(mock_db)
        papers, total = await service.list_papers(page=1, page_size=20)
        
        assert total >= 0
        assert isinstance(papers, list)

    @pytest.mark.asyncio
    async def test_list_papers_with_filter(self, mock_db, mock_paper):
        """带筛选条件的列表查询"""
        from app.services.paper_service import PaperService
        
        # Mock 列表查询结果
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = [mock_paper]
        
        # Mock 计数查询结果
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1
        
        # 根据查询参数类型返回不同结果
        async def mock_execute(query):
            if hasattr(query, 'subquery'):
                return mock_count_result
            return mock_list_result
        
        mock_db.execute = mock_execute
        
        service = PaperService(mock_db)
        papers, total = await service.list_papers(
            subject="数学",
            status="draft",
            keyword="月考"
        )
        
        assert total >= 0

    @pytest.mark.asyncio
    async def test_get_paper_by_id(self, mock_db, mock_paper):
        """根据ID获取试卷"""
        from app.services.paper_service import PaperService
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_paper
        mock_db.execute.return_value = mock_result
        
        service = PaperService(mock_db)
        paper = await service.get_paper_by_id(mock_paper.id)
        
        assert paper is not None
        assert paper.title == "测试试卷"

    @pytest.mark.asyncio
    async def test_delete_paper_soft_delete(self, mock_db, mock_paper):
        """软删除试卷"""
        from app.services.paper_service import PaperService
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_paper
        mock_db.execute.return_value = mock_result
        
        service = PaperService(mock_db)
        result = await service.delete_paper(mock_paper.id)
        
        assert result is True
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_publish_paper(self, mock_db, mock_paper):
        """发布试卷"""
        from app.services.paper_service import PaperService
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_paper
        mock_db.execute.return_value = mock_result
        
        service = PaperService(mock_db)
        paper = await service.publish_paper(mock_paper.id)
        
        assert paper.status == "published"
        mock_db.commit.assert_called()


# =============================================================================
# Test Class 8: 端到端工作流测试
# =============================================================================

class TestPaperGenerationWorkflow:
    """端到端组卷工作流测试"""

    @pytest.mark.asyncio
    async def test_full_generation_workflow(self, mock_db):
        """完整生成工作流"""
        from app.services.paper_service import PaperService
        from app.schemas.paper import PaperGenerateRequest
        
        # Mock 题目查询
        mock_questions = [
            MagicMock(
                id=uuid4(), content=f"题目{i}", question_type="single",
                options=["A", "B", "C", "D"], answer="A", analysis="",
                difficulty=(i % 5) + 1, cognitive_level="L3",
                knowledge_points=["二次函数"], score=5.0,
                is_deleted=False, review_status="approved",
                has_answer=True, usage_count=0,
            )
            for i in range(30)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_questions
        mock_db.execute.return_value = mock_result
        
        service = PaperService(mock_db)
        request = PaperGenerateRequest(
            title="月考试卷",
            subject="数学",
            grade_level="高一",
            paper_type="exam",
            total_count=20,
            target_knowledge_points=["二次函数"],
            difficulty_distribution={"1": 0.2, "2": 0.4, "3": 0.3, "4": 0.1},
        )
        
        result = await service.generate_paper(request, uuid4())
        
        assert result is not None
        assert len(result.questions) <= 30
        assert result.difficulty_distribution is not None

    @pytest.mark.asyncio
    async def test_diagnostic_workflow(self, mock_db):
        """诊断组卷工作流"""
        from app.services.paper_service import PaperService
        from app.schemas.paper import DiagnosticGenerateRequest
        
        mock_questions = [
            MagicMock(
                id=uuid4(), content="题", question_type="single",
                options=[], answer="A", analysis="", difficulty=1,
                cognitive_level="L2", knowledge_points=["函数"],
                score=5.0, is_deleted=False, review_status="approved",
                has_answer=True, usage_count=0,
            )
            for _ in range(20)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_questions
        mock_db.execute.return_value = mock_result
        
        service = PaperService(mock_db)
        request = DiagnosticGenerateRequest(
            title="诊断测试",
            student_id=str(uuid4()),
            diagnosis_report={
                "weak_points": ["函数"],
                "mastery_levels": {"函数": 0.3}
            },
            total_count=15,
        )
        
        result = await service.generate_diagnostic_paper(request, uuid4())
        
        assert result is not None


# =============================================================================
# 运行说明
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
