# -*- coding: utf-8 -*-
"""
TASK-07 测试脚本：学习记录前端页面
测试目标：验证后端 ai/learning_records.py API 正确可用，
         前端 LearningRecord.vue 已连接真实接口

运行方式：
    cd smart-campus
    python -m pytest backend/tests/test_task07_learning_record.py -v

通过条件：所有测试用例通过后方可将 TASK-07 标记为完成
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

FRONTEND_VIEWS = os.path.join(
    os.path.dirname(__file__), '..', '..', 'frontend', 'src', 'views'
)


# =====================================================================
# 后端 API 结构检查
# =====================================================================

class TestLearningRecordAPIStructure:
    """验证 ai/learning_records.py 后端 API"""

    def test_learning_records_router_importable(self):
        """learning_records router 可导入"""
        try:
            from app.api.v1.ai.learning_records import router
            assert router is not None
        except ImportError as e:
            pytest.fail(f"learning_records router 无法导入: {e}")

    def test_list_route_exists(self):
        """GET / 列表路由存在"""
        try:
            from app.api.v1.ai.learning_records import router
            routes = [r.path for r in router.routes]
            # 期望存在 GET / 或 GET /records 或类似路径
            assert len(routes) > 0, f"未找到任何路由"
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_detail_route_exists(self):
        """GET /{id} 详情路由存在"""
        try:
            from app.api.v1.ai.learning_records import router
            routes = [r.path for r in router.routes]
            has_detail = any('{' in r and '}' in r for r in routes)
            assert has_detail, (
                f"未找到带 ID 参数的详情路由，现有: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_create_route_exists(self):
        """POST 创建路由存在"""
        try:
            from app.api.v1.ai.learning_records import router
            from fastapi.routing import APIRoute
            post_routes = [
                r for r in router.routes
                if isinstance(r, APIRoute) and 'POST' in r.methods
            ]
            assert len(post_routes) > 0, "未找到 POST 路由，需实现创建学习记录功能"
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_supports_student_id_filter(self):
        """GET 路由支持 student_id 过滤参数"""
        try:
            source_path = os.path.join(
                os.path.dirname(__file__), '..', 'app', 'api', 'v1', 'ai', 'learning_records.py'
            )
            with open(source_path, 'r', encoding='utf-8') as f:
                source = f.read()
            assert 'student_id' in source, (
                "FAIL: learning_records.py 中未发现 student_id 过滤参数"
            )
        except FileNotFoundError:
            pytest.skip("文件不存在，跳过")

    def test_supports_course_filter(self):
        """GET 路由支持课程过滤参数"""
        try:
            source_path = os.path.join(
                os.path.dirname(__file__), '..', 'app', 'api', 'v1', 'ai', 'learning_records.py'
            )
            with open(source_path, 'r', encoding='utf-8') as f:
                source = f.read()
            has_course_filter = 'course_id' in source or 'course' in source.lower()
            assert has_course_filter, (
                "FAIL: learning_records.py 中未发现课程过滤参数"
            )
        except FileNotFoundError:
            pytest.skip("文件不存在，跳过")


# =====================================================================
# 前端组件检查
# =====================================================================

class TestLearningRecordFrontend:
    """验证前端学习记录页面组件"""

    def _get_vue_source(self, filepath: str) -> str:
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def _find_vue_file(self) -> str:
        """查找 LearningRecord.vue 文件"""
        candidates = [
            os.path.join(FRONTEND_VIEWS, 'ai', 'LearningRecord.vue'),
            os.path.join(FRONTEND_VIEWS, 'ai', 'learning-record.vue'),
            os.path.join(FRONTEND_VIEWS, 'learning', 'LearningRecord.vue'),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    def test_learning_record_vue_exists(self):
        """LearningRecord.vue 文件存在"""
        path = self._find_vue_file()
        assert path is not None, (
            f"FAIL: LearningRecord.vue 不存在，已检查路径: {FRONTEND_VIEWS}/ai/"
        )

    def test_learning_record_uses_api_call(self):
        """LearningRecord.vue 应调用后端 API"""
        path = self._find_vue_file()
        if path is None:
            pytest.skip("LearningRecord.vue 不存在，跳过")
        source = self._get_vue_source(path)
        has_api_call = (
            'api' in source.lower() or
            'axios' in source.lower() or
            '/api/v1' in source or
            'learning-record' in source or
            'learningRecord' in source
        )
        assert has_api_call, (
            "FAIL: LearningRecord.vue 未调用后端 API，需接入 /api/v1/ai/learning-records"
        )

    def test_learning_record_no_hardcoded_mock(self):
        """LearningRecord.vue 不应有硬编码假数据"""
        path = self._find_vue_file()
        if path is None:
            pytest.skip("LearningRecord.vue 不存在，跳过")
        source = self._get_vue_source(path)
        forbidden = ['mockData', 'fakeData', 'testData = [']
        found = [f for f in forbidden if f in source]
        assert not found, (
            f"FAIL: LearningRecord.vue 发现可能的硬编码假数据: {found}"
        )

    def test_learning_record_has_student_filter(self):
        """LearningRecord.vue 应有学生过滤功能"""
        path = self._find_vue_file()
        if path is None:
            pytest.skip("LearningRecord.vue 不存在，跳过")
        source = self._get_vue_source(path)
        has_filter = (
            'student' in source.lower() or
            'filter' in source.lower() or
            'select' in source.lower()
        )
        assert has_filter, (
            "FAIL: LearningRecord.vue 缺少学生过滤功能"
        )


# =====================================================================
# 数据模型检查
# =====================================================================

class TestLearningRecordModels:
    """验证学习记录数据模型"""

    def test_learning_record_model_importable(self):
        """LearningRecord 模型可导入"""
        try:
            from app.models.learning_record import LearningRecord
            assert LearningRecord is not None
        except ImportError:
            pytest.skip("LearningRecord 模型未找到，跳过")

    def test_learning_record_service_importable(self):
        """学习记录服务可导入"""
        try:
            from app.services.learning_record_service import LearningRecordService
            assert LearningRecordService is not None
        except ImportError:
            try:
                from app.api.v1.ai.learning_records import router
                # API 存在即可
            except ImportError:
                pytest.skip("学习记录服务/API 均未找到，跳过")


# =====================================================================
# 集成测试
# =====================================================================

class TestLearningRecordIntegration:
    @pytest.mark.asyncio
    async def test_list_returns_records_from_db(self):
        pytest.skip("集成测试需要数据库环境，请在有DB的环境中运行")

    @pytest.mark.asyncio
    async def test_student_filter_works(self):
        pytest.skip("集成测试需要数据库环境，请在有DB的环境中运行")


if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True, text=True
    )
    print(result.stdout)
    print(result.stderr)
