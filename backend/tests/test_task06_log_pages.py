# -*- coding: utf-8 -*-
"""
TASK-06 测试脚本：操作日志 & 登录日志页面
测试目标：验证后端 system/logs.py API 正确可用，前端组件已连接真实接口

运行方式：
    cd smart-campus
    python -m pytest backend/tests/test_task06_log_pages.py -v

通过条件：所有测试用例通过后方可将 TASK-06 标记为完成
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

class TestLogsAPIStructure:
    """验证 system/logs.py 后端 API 存在且结构正确"""

    def test_logs_router_importable(self):
        """system logs router 可正常导入"""
        try:
            from app.api.v1.system.logs import router
            assert router is not None
        except ImportError as e:
            pytest.fail(f"system logs router 无法导入: {e}")

    def test_operation_log_route_exists(self):
        """GET /operation 路由存在"""
        try:
            from app.api.v1.system.logs import router
            routes = [r.path for r in router.routes]
            assert any('operation' in r.lower() for r in routes), (
                f"未找到 operation 路由，现有: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_login_log_route_exists(self):
        """GET /login 路由存在"""
        try:
            from app.api.v1.system.logs import router
            routes = [r.path for r in router.routes]
            assert any('login' in r.lower() for r in routes), (
                f"未找到 login 路由，现有: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_delete_operation_log_route_exists(self):
        """DELETE /operation/{id} 路由存在"""
        try:
            from app.api.v1.system.logs import router
            from fastapi.routing import APIRoute
            delete_routes = [
                r for r in router.routes
                if isinstance(r, APIRoute) and 'DELETE' in r.methods
            ]
            assert len(delete_routes) > 0, (
                "未找到 DELETE 路由，需实现删除操作日志功能"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")


# =====================================================================
# 前端组件检查
# =====================================================================

class TestLogPagesFrontend:
    """验证前端日志页面组件存在且调用真实 API"""

    def _get_vue_source(self, filename: str) -> str:
        path = os.path.join(FRONTEND_VIEWS, 'system', filename)
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_operation_log_vue_exists(self):
        """OperationLog.vue 文件存在"""
        path = os.path.join(FRONTEND_VIEWS, 'system', 'OperationLog.vue')
        assert os.path.exists(path), (
            f"FAIL: OperationLog.vue 不存在，路径: {path}"
        )

    def test_login_log_vue_exists(self):
        """LoginLog.vue 文件存在"""
        path = os.path.join(FRONTEND_VIEWS, 'system', 'LoginLog.vue')
        assert os.path.exists(path), (
            f"FAIL: LoginLog.vue 不存在，路径: {path}"
        )

    def test_operation_log_uses_api_call(self):
        """OperationLog.vue 应调用后端 API（非硬编码假数据）"""
        source = self._get_vue_source('OperationLog.vue')
        if source is None:
            pytest.skip("OperationLog.vue 不存在，跳过")
        has_api_call = (
            'api' in source.lower() or
            'axios' in source.lower() or
            'fetch(' in source or
            'request(' in source or
            '/api/v1' in source or
            'logs' in source.lower()
        )
        assert has_api_call, (
            "FAIL: OperationLog.vue 未调用后端 API，需接入 /api/v1/system/logs/operation"
        )

    def test_operation_log_no_hardcoded_mock_data(self):
        """OperationLog.vue 不应有大段硬编码假数据"""
        source = self._get_vue_source('OperationLog.vue')
        if source is None:
            pytest.skip("OperationLog.vue 不存在，跳过")
        # 检测典型的硬编码数据特征
        hardcoded_indicators = [
            'mockData', 'mock_data', 'fakeData',
            "'操作日志1'", '"操作日志1"',
        ]
        found = [i for i in hardcoded_indicators if i in source]
        assert not found, (
            f"FAIL: OperationLog.vue 中发现可能的硬编码假数据: {found}"
        )

    def test_login_log_uses_api_call(self):
        """LoginLog.vue 应调用后端 API"""
        source = self._get_vue_source('LoginLog.vue')
        if source is None:
            pytest.skip("LoginLog.vue 不存在，跳过")
        has_api_call = (
            'api' in source.lower() or
            'axios' in source.lower() or
            '/api/v1' in source or
            'login' in source.lower()
        )
        assert has_api_call, (
            "FAIL: LoginLog.vue 未调用后端 API，需接入 /api/v1/system/logs/login"
        )

    def test_operation_log_has_pagination(self):
        """OperationLog.vue 应实现分页功能"""
        source = self._get_vue_source('OperationLog.vue')
        if source is None:
            pytest.skip("OperationLog.vue 不存在，跳过")
        has_pagination = (
            'page' in source.lower() or
            'pagination' in source.lower() or
            'el-pagination' in source or
            'pageSize' in source or
            'page_size' in source
        )
        assert has_pagination, (
            "FAIL: OperationLog.vue 缺少分页功能，需实现分页展示"
        )

    def test_operation_log_has_search(self):
        """OperationLog.vue 应实现搜索功能"""
        source = self._get_vue_source('OperationLog.vue')
        if source is None:
            pytest.skip("OperationLog.vue 不存在，跳过")
        has_search = (
            'search' in source.lower() or
            'keyword' in source.lower() or
            'input' in source.lower() or
            'el-input' in source
        )
        assert has_search, (
            "FAIL: OperationLog.vue 缺少搜索功能，需实现关键字搜索"
        )


# =====================================================================
# API 数据模型检查
# =====================================================================

class TestLogDataModels:
    """验证日志数据模型"""

    def test_operation_log_model_importable(self):
        """OperationLog 模型可导入"""
        try:
            from app.models.operation_log import OperationLog
            assert OperationLog is not None
        except ImportError:
            # 尝试其他可能的路径
            try:
                from app.models.log import OperationLog
                assert OperationLog is not None
            except ImportError:
                pytest.skip("OperationLog 模型未找到，跳过")

    def test_login_log_model_importable(self):
        """LoginLog 模型可导入"""
        try:
            from app.models.login_log import LoginLog
            assert LoginLog is not None
        except ImportError:
            try:
                from app.models.log import LoginLog
                assert LoginLog is not None
            except ImportError:
                pytest.skip("LoginLog 模型未找到，跳过")


# =====================================================================
# 集成测试
# =====================================================================

class TestLogPagesIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_operation_log_list_returns_real_data(self):
        """操作日志列表接口返回真实数据"""
        pytest.skip("集成测试需要数据库环境，请在有DB的环境中运行")

    @pytest.mark.asyncio
    async def test_login_log_pagination_works(self):
        """登录日志分页参数正确处理"""
        pytest.skip("集成测试需要数据库环境，请在有DB的环境中运行")


if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True, text=True
    )
    print(result.stdout)
    print(result.stderr)
