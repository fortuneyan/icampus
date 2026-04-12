"""
T11 测试：能力画像 + 知识图谱 + 诊断报告

覆盖：
1. get_ability_profile — 多维能力分析
2. get_ability_radar  — 雷达图数据
3. get_knowledge_graph — 知识图谱构建
4. generate_diagnosis_report — 综合诊断报告
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestAIServiceAbilityProfile:
    """能力画像分析测试"""

    def setup_method(self):
        import sys
        mods = [k for k in sys.modules.keys() if 'app.services.ai_service' in k]
        for m in mods:
            sys.modules.pop(m, None)

    @pytest.mark.asyncio
    async def test_ability_profile_with_scores(self):
        """测试：成绩数据存在时能正确计算能力维度"""
        from app.services.ai_service import AIService

        mock_db = AsyncMock()

        # 构造真实的 mock 成绩对象
        mock_score1 = MagicMock()
        mock_score1.course_id = uuid4()
        mock_score1.score = 85.0
        mock_score1.score_type = "选择题"
        mock_score1.recorded_at = datetime.now()

        mock_score2 = MagicMock()
        mock_score2.course_id = uuid4()
        mock_score2.score = 72.0
        mock_score2.score_type = "解答题"
        mock_score2.recorded_at = datetime.now()

        mock_score3 = MagicMock()
        mock_score3.course_id = uuid4()
        mock_score3.score = 55.0
        mock_score3.score_type = "应用题"
        mock_score3.recorded_at = datetime.now()

        mock_scores = [mock_score1, mock_score2, mock_score3]

        # 成绩查询 mock：正确设置 scalars().all() 链
        mock_score_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_scores
        mock_score_result.scalars.return_value = mock_scalars

        # 学习记录查询 mock（空结果）
        mock_rec_result = MagicMock()
        mock_rec_scalars = MagicMock()
        mock_rec_scalars.all.return_value = []
        mock_rec_result.scalars.return_value = mock_rec_scalars

        # 根据查询内容返回对应 mock
        async def mock_execute(q):
            query_str = str(q).lower()
            if "learning_record" in query_str:
                return mock_rec_result
            return mock_score_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        service = AIService(mock_db)
        student_id = uuid4()

        profile = await service.get_ability_profile(student_id)

        # 断言
        assert profile is not None
        assert profile.student_id == str(student_id)
        # 平均分 = (85+72+55)/3 ≈ 70.67
        assert profile.overall_score == pytest.approx(70.67, abs=1.0)
        assert isinstance(profile.dimensions, list)
        assert len(profile.dimensions) >= 1
        assert isinstance(profile.strengths, list)
        assert isinstance(profile.weaknesses, list)
        assert isinstance(profile.improvement_suggestions, list)
        assert profile.generated_at is not None

    @pytest.mark.asyncio
    async def test_ability_profile_no_data(self):
        """测试：无成绩数据时返回默认值"""
        from app.services.ai_service import AIService

        mock_db = AsyncMock()

        # 成绩查询返回空
        mock_score_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_score_result.scalars.return_value = mock_scalars

        # 记录查询也返回空
        mock_rec_result = MagicMock()
        mock_rec_scalars = MagicMock()
        mock_rec_scalars.all.return_value = []
        mock_rec_result.scalars.return_value = mock_rec_scalars

        async def mock_execute(q):
            query_str = str(q).lower()
            if "learning_record" in query_str:
                return mock_rec_result
            return mock_score_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        service = AIService(mock_db)
        student_id = uuid4()

        profile = await service.get_ability_profile(student_id)

        assert profile is not None
        assert profile.overall_score == 0
        assert isinstance(profile.dimensions, list)
        assert len(profile.dimensions) == 1  # 只有综合能力
        assert profile.dimensions[0].name == "综合能力"


class TestAIServiceAbilityRadar:
    """能力雷达图测试"""

    def setup_method(self):
        import sys
        mods = [k for k in sys.modules.keys() if 'app.services.ai_service' in k]
        for m in mods:
            sys.modules.pop(m, None)

    @pytest.mark.asyncio
    async def test_ability_radar_returns_valid_data(self):
        """测试：雷达图数据返回有效结构"""
        from app.services.ai_service import AIService

        mock_db = AsyncMock()

        mock_score = MagicMock()
        mock_score.course_id = uuid4()
        mock_score.score = 78.0
        mock_score.score_type = "选择题"

        mock_score_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_score]
        mock_score_result.scalars.return_value = mock_scalars

        mock_rec_result = MagicMock()
        mock_rec_scalars = MagicMock()
        mock_rec_scalars.all.return_value = []
        mock_rec_result.scalars.return_value = mock_rec_scalars

        async def mock_execute(q):
            query_str = str(q).lower()
            if "learning_record" in query_str:
                return mock_rec_result
            return mock_score_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        service = AIService(mock_db)
        radar = await service.get_ability_radar(uuid4())

        assert radar is not None
        assert radar.student_id is not None
        assert isinstance(radar.indicators, list)
        if radar.indicators:
            assert radar.indicators[0].name is not None
            assert 0 <= radar.indicators[0].value <= 100
        assert radar.avg_score is not None
        assert radar.highest_dimension is not None
        assert radar.lowest_dimension is not None


class TestAIServiceKnowledgeGraph:
    """知识图谱测试"""

    def setup_method(self):
        import sys
        mods = [k for k in sys.modules.keys() if 'app.services.ai_service' in k]
        for m in mods:
            sys.modules.pop(m, None)

    @pytest.mark.asyncio
    async def test_knowledge_graph_structure(self):
        """测试：知识图谱返回正确的节点/边结构"""
        from app.services.ai_service import AIService

        mock_db = AsyncMock()

        mock_score_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_score_result.scalars.return_value = mock_scalars

        mock_rec_result = MagicMock()
        mock_rec_scalars = MagicMock()
        mock_rec_scalars.all.return_value = []
        mock_rec_result.scalars.return_value = mock_rec_scalars

        async def mock_execute(q):
            query_str = str(q).lower()
            if "learning_record" in query_str:
                return mock_rec_result
            return mock_score_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        service = AIService(mock_db)
        course_id = uuid4()
        course_name = "数学"

        graph = await service.get_knowledge_graph(uuid4(), course_id, course_name)

        assert graph is not None
        assert graph.student_id is not None
        assert graph.course_name == "数学"
        assert isinstance(graph.nodes, list)
        assert len(graph.nodes) > 0  # 至少有知识节点
        assert isinstance(graph.edges, list)
        assert isinstance(graph.weakest_nodes, list)
        assert isinstance(graph.learning_frontier, list)

    @pytest.mark.asyncio
    async def test_knowledge_graph_nodes_have_required_fields(self):
        """测试：每个节点包含必要字段"""
        from app.services.ai_service import AIService

        mock_db = AsyncMock()

        mock_score_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_score_result.scalars.return_value = mock_scalars

        mock_rec_result = MagicMock()
        mock_rec_scalars = MagicMock()
        mock_rec_scalars.all.return_value = []
        mock_rec_result.scalars.return_value = mock_rec_scalars

        async def mock_execute(q):
            query_str = str(q).lower()
            if "learning_record" in query_str:
                return mock_rec_result
            return mock_score_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        service = AIService(mock_db)
        graph = await service.get_knowledge_graph(uuid4())

        for node in graph.nodes:
            assert node.node_id is not None
            assert node.name is not None
            assert 0 <= node.mastery <= 100
            assert 0 <= node.difficulty <= 5
            assert 0 <= node.importance <= 100
            assert isinstance(node.prerequisites, list)


class TestAIServiceDiagnosisReport:
    """综合诊断报告测试"""

    def setup_method(self):
        import sys
        mods = [k for k in sys.modules.keys() if 'app.services.ai_service' in k]
        for m in mods:
            sys.modules.pop(m, None)

    @pytest.mark.asyncio
    async def test_diagnosis_report_combines_all_data(self):
        """测试：诊断报告整合能力画像+知识图谱+雷达图"""
        from app.services.ai_service import AIService

        mock_db = AsyncMock()

        mock_score = MagicMock()
        mock_score.course_id = uuid4()
        mock_score.score = 75.0
        mock_score.score_type = "选择题"
        mock_score.recorded_at = datetime.now()

        mock_score_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_score]
        mock_score_result.scalars.return_value = mock_scalars

        mock_rec_result = MagicMock()
        mock_rec_scalars = MagicMock()
        mock_rec_scalars.all.return_value = []
        mock_rec_result.scalars.return_value = mock_rec_scalars

        async def mock_execute(q):
            query_str = str(q).lower()
            if "learning_record" in query_str:
                return mock_rec_result
            return mock_score_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        service = AIService(mock_db)
        student_id = uuid4()

        report = await service.generate_diagnosis_report(
            student_id=student_id,
            course_id=uuid4(),
            course_name="数学",
            include_ability=True,
            include_knowledge_graph=True,
        )

        assert report is not None
        assert report.student_id == str(student_id)
        assert report.report_id is not None
        assert report.ability_profile is not None
        assert report.knowledge_graph is not None
        assert report.radar_data is not None
        assert isinstance(report.recommendations, list)
        assert report.report_date is not None

    @pytest.mark.asyncio
    async def test_diagnosis_report_without_ability(self):
        """测试：仅包含知识图谱的报告"""
        from app.services.ai_service import AIService

        mock_db = AsyncMock()

        mock_score_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_score_result.scalars.return_value = mock_scalars

        mock_rec_result = MagicMock()
        mock_rec_scalars = MagicMock()
        mock_rec_scalars.all.return_value = []
        mock_rec_result.scalars.return_value = mock_rec_scalars

        async def mock_execute(q):
            query_str = str(q).lower()
            if "learning_record" in query_str:
                return mock_rec_result
            return mock_score_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        service = AIService(mock_db)

        report = await service.generate_diagnosis_report(
            student_id=uuid4(),
            include_ability=False,
            include_knowledge_graph=True,
        )

        assert report.ability_profile is None
        assert report.knowledge_graph is not None
        assert report.radar_data is not None


class TestLearningDiagnosisAPI:
    """LearningDiagnosis API 端点测试"""

    @pytest.mark.asyncio
    async def test_ability_profile_endpoint_static(self):
        """静态检查：/ability/{student_id} 端点定义存在"""
        from app.api.v1.ai.learning_diagnosis import router

        routes = [r.path for r in router.routes]
        assert "/ability/{student_id}" in routes

    @pytest.mark.asyncio
    async def test_ability_radar_endpoint_static(self):
        """静态检查：/radar/{student_id} 端点定义存在"""
        from app.api.v1.ai.learning_diagnosis import router

        routes = [r.path for r in router.routes]
        assert "/radar/{student_id}" in routes

    @pytest.mark.asyncio
    async def test_knowledge_graph_endpoint_static(self):
        """静态检查：/knowledge-graph/{student_id} 端点定义存在"""
        from app.api.v1.ai.learning_diagnosis import router

        routes = [r.path for r in router.routes]
        assert "/knowledge-graph/{student_id}" in routes

    @pytest.mark.asyncio
    async def test_report_endpoint_static(self):
        """静态检查：/report POST 端点定义存在"""
        from app.api.v1.ai.learning_diagnosis import router

        routes = [r.path for r in router.routes]
        assert "/report" in routes

    @pytest.mark.asyncio
    async def test_all_endpoints_http_methods(self):
        """验证所有新端点都是正确的 HTTP 方法"""
        from app.api.v1.ai.learning_diagnosis import router

        route_map = {r.path: r.methods for r in router.routes}

        assert "GET" in route_map.get("/ability/{student_id}", set())
        assert "GET" in route_map.get("/radar/{student_id}", set())
        assert "GET" in route_map.get("/knowledge-graph/{student_id}", set())
        assert "POST" in route_map.get("/report", set())


class TestSchemas:
    """Schema 模型测试"""

    def test_ability_dimension_schema(self):
        """测试 AbilityDimension schema 验证"""
        from app.schemas.ai import AbilityDimension

        dim = AbilityDimension(
            name="计算能力",
            score=85.5,
            level="优秀",
            trend="up",
            evidence=["基于3次选择题平均得分"],
        )
        assert dim.name == "计算能力"
        assert dim.score == 85.5
        assert dim.trend == "up"

    def test_ability_profile_schema(self):
        """测试 AbilityProfile schema"""
        from app.schemas.ai import AbilityProfile, AbilityDimension

        profile = AbilityProfile(
            student_id="test-123",
            overall_score=78.0,
            dimensions=[
                AbilityDimension(name="计算能力", score=85.0, level="优秀", trend="up"),
            ],
            strengths=["计算能力"],
            weaknesses=["应用题"],
            improvement_suggestions=["建议加强练习"],
            generated_at="2026-04-12T00:00:00",
        )
        assert profile.student_id == "test-123"
        assert profile.overall_score == 78.0
        assert len(profile.dimensions) == 1

    def test_knowledge_graph_schema(self):
        """测试 KnowledgeGraph schema"""
        from app.schemas.ai import KnowledgeGraph, KnowledgeNode, KnowledgeEdge

        graph = KnowledgeGraph(
            student_id="test-123",
            nodes=[
                KnowledgeNode(
                    node_id="K001",
                    name="基础运算",
                    mastery=85.0,
                    difficulty=1.0,
                    importance=90,
                )
            ],
            edges=[
                KnowledgeEdge(source="K001", target="K002", relation="prerequisite")
            ],
            weakest_nodes=["K005"],
            learning_frontier=["K003"],
            generated_at="2026-04-12T00:00:00",
        )
        assert graph.student_id == "test-123"
        assert len(graph.nodes) == 1
        assert len(graph.edges) == 1
        assert graph.weakest_nodes == ["K005"]

    def test_diagnosis_report_schema(self):
        """测试 DiagnosisReport schema"""
        from app.schemas.ai import DiagnosisReport

        report = DiagnosisReport(
            student_id="test-123",
            report_id="report-001",
            recommendations=[
                {"type": "ability", "text": "建议加强练习", "priority": "high"}
            ],
            report_date="2026-04-12T00:00:00",
        )
        assert report.student_id == "test-123"
        assert report.report_id == "report-001"
        assert len(report.recommendations) == 1
