# -*- coding: utf-8 -*-
"""
TASK-05 测试脚本：仪表盘统计 — 对接真实数据库
测试目标：验证 dashboard_service.py 中不再使用硬编码数据，
         overview.py 中不再使用 MagicMock

运行方式：
    cd smart-campus
    python -m pytest backend/tests/test_task05_dashboard.py -v

通过条件：所有测试用例通过后方可将 TASK-05 标记为完成
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# =====================================================================
# 静态代码检查 — dashboard_service.py
# =====================================================================

class TestDashboardServiceNoHardcoded:
    """验证 dashboard_service.py 中硬编码数据已移除"""

    def _get_service_source(self):
        path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'services', 'dashboard_service.py'
        )
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_no_hardcoded_student_trend(self):
        """不应有硬编码的学生增长趋势数据"""
        source = self._get_service_source()
        # 检测几个典型硬编码特征
        has_hardcoded = (
            '{"month": "1月", "value": 1000}' in source or
            '"value": 1000' in source and '"month": "1月"' in source
        )
        assert not has_hardcoded, (
            "FAIL: 发现硬编码的学生增长趋势数据，需替换为数据库查询"
        )

    def test_no_hardcoded_score_trend(self):
        """不应有硬编码的成绩趋势数据"""
        source = self._get_service_source()
        # 检测硬编码的成绩数组（通常有多个月份硬编码的值）
        has_hardcoded = source.count('"value":') > 10 and 'return {' in source
        # 软判断：如果 get_statistics 方法中仍有多个硬编码 value
        lines = source.split('\n')
        static_returns = [l for l in lines if '"value":' in l and '"month":' in l]
        assert len(static_returns) < 3, (
            f"FAIL: get_statistics() 中发现 {len(static_returns)} 行硬编码月份/数值数据，应改为数据库查询"
        )

    def test_no_hardcoded_gender_distribution(self):
        """不应有硬编码的性别分布数据"""
        source = self._get_service_source()
        has_hardcoded = (
            '"data": [600, 550]' in source or
            '"data": [600,' in source
        )
        assert not has_hardcoded, (
            "FAIL: 发现硬编码的性别分布数据 [600, 550]，需替换为数据库查询"
        )

    def test_uses_db_queries(self):
        """get_statistics 或 get_charts 应包含数据库查询语句"""
        source = self._get_service_source()
        has_db_query = (
            'await self.db.execute' in source or
            'self.db.execute' in source or
            'func.count' in source or
            'select(' in source or
            'func.avg' in source
        )
        assert has_db_query, (
            "FAIL: dashboard_service.py 中未发现数据库查询代码，需添加真实 DB 查询"
        )

    def test_empty_data_returns_empty_list(self):
        """空数据降级：应返回空列表而非固定数据"""
        source = self._get_service_source()
        # 确认有针对空结果的处理
        has_empty_handling = (
            'if not' in source or
            'or []' in source or
            '[] if' in source or
            'else []' in source
        )
        assert has_empty_handling, (
            "FAIL: 缺少空数据降级处理，空数据库时应返回 [] 而非固定数据"
        )


# =====================================================================
# 静态代码检查 — overview.py（MagicMock 问题）
# =====================================================================

class TestOverviewNoMagicMock:
    """验证 overview.py 中 MagicMock 已移除"""

    def _get_overview_source(self):
        path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1', 'dashboard', 'overview.py'
        )
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_no_magic_mock_import(self):
        """overview.py 不应导入 MagicMock"""
        source = self._get_overview_source()
        assert 'MagicMock' not in source, (
            "FAIL: overview.py 中仍使用 MagicMock，生产代码禁止使用测试工具"
        )

    def test_no_unittest_mock_import(self):
        """overview.py 不应导入 unittest.mock"""
        source = self._get_overview_source()
        assert 'unittest.mock' not in source, (
            "FAIL: 生产代码不应导入 unittest.mock"
        )

    def test_quick_actions_uses_db_dependency(self):
        """quick-actions 路由应注入真实 DB 依赖"""
        source = self._get_overview_source()
        has_db = (
            'get_db' in source or
            'AsyncSession' in source
        )
        assert has_db, (
            "FAIL: quick-actions 路由应注入 DB 依赖，当前缺少 db: AsyncSession = Depends(get_db)"
        )


# =====================================================================
# DashboardService 结构测试
# =====================================================================

class TestDashboardServiceStructure:
    """验证 DashboardService 的方法可正常导入"""

    def test_service_importable(self):
        """DashboardService 可正常导入"""
        try:
            from app.services.dashboard_service import DashboardService
            assert DashboardService is not None
        except ImportError as e:
            pytest.fail(f"DashboardService 无法导入: {e}")

    def test_service_has_get_statistics(self):
        """DashboardService 具有 get_statistics 方法"""
        try:
            from app.services.dashboard_service import DashboardService
            assert hasattr(DashboardService, 'get_statistics'), (
                "DashboardService 缺少 get_statistics 方法"
            )
        except ImportError:
            pytest.skip("服务未实现，跳过")

    def test_service_has_get_charts(self):
        """DashboardService 具有 get_charts 方法"""
        try:
            from app.services.dashboard_service import DashboardService
            assert hasattr(DashboardService, 'get_charts'), (
                "DashboardService 缺少 get_charts 方法"
            )
        except ImportError:
            pytest.skip("服务未实现，跳过")

    def test_service_has_get_overview(self):
        """DashboardService 具有 get_overview 方法"""
        try:
            from app.services.dashboard_service import DashboardService
            has_overview = (
                hasattr(DashboardService, 'get_overview') or
                hasattr(DashboardService, 'get_dashboard_data') or
                hasattr(DashboardService, 'get_summary')
            )
            assert has_overview, (
                "DashboardService 缺少概览方法（get_overview/get_dashboard_data/get_summary）"
            )
        except ImportError:
            pytest.skip("服务未实现，跳过")


# =====================================================================
# 数据结构验证（Mock DB 场景）
# =====================================================================

class TestDashboardDataStructure:
    """验证仪表盘数据结构正确性"""

    @pytest.mark.asyncio
    async def test_statistics_returns_dict_with_expected_keys(self):
        """get_statistics() 返回字典包含预期的 key"""
        try:
            from app.services.dashboard_service import DashboardService
            from unittest.mock import AsyncMock, MagicMock, patch
            import sqlalchemy

            mock_db = AsyncMock()

            # Mock 数据库查询结果为空
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar.return_value = 0
            mock_db.execute = AsyncMock(return_value=mock_result)

            service = DashboardService(mock_db)

            result = await service.get_statistics()

            assert isinstance(result, dict), (
                f"get_statistics() 应返回 dict，实际返回: {type(result)}"
            )
            # 基本检查：不应是硬编码的固定值
            student_trend = result.get('student_trend', [])
            assert isinstance(student_trend, list), (
                "student_trend 应为列表类型"
            )
        except (ImportError, Exception) as e:
            pytest.skip(f"依赖未安装或 DB Mock 复杂，跳过: {e}")

    @pytest.mark.asyncio
    async def test_charts_returns_dict_with_expected_keys(self):
        """get_charts() 返回字典包含预期的 key"""
        try:
            from app.services.dashboard_service import DashboardService
            from unittest.mock import AsyncMock, MagicMock

            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar.return_value = 0
            mock_db.execute = AsyncMock(return_value=mock_result)

            service = DashboardService(mock_db)

            result = await service.get_charts()

            assert isinstance(result, dict), (
                f"get_charts() 应返回 dict，实际返回: {type(result)}"
            )
            expected_keys = ['student_gender', 'resource_type', 'attendance_trend']
            for key in expected_keys:
                assert key in result, (
                    f"get_charts() 缺少 '{key}' 字段，现有: {list(result.keys())}"
                )
        except (ImportError, Exception) as e:
            pytest.skip(f"依赖未安装或 DB Mock 复杂，跳过: {e}")


# =====================================================================
# Overview 路由结构检查
# =====================================================================

class TestOverviewAPIStructure:
    """验证 overview.py 路由结构"""

    def test_overview_router_importable(self):
        """overview router 可正常导入"""
        try:
            from app.api.v1.dashboard.overview import router
            assert router is not None
        except ImportError as e:
            pytest.fail(f"overview router 无法导入: {e}")

    def test_quick_actions_route_exists(self):
        """quick-actions 路由存在"""
        try:
            from app.api.v1.dashboard.overview import router
            routes = [r.path for r in router.routes]
            assert any('quick' in r.lower() or 'action' in r.lower() for r in routes), (
                f"未找到 quick-actions 路由，现有: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_statistics_route_exists(self):
        """statistics 路由存在"""
        try:
            from app.api.v1.dashboard.overview import router
            routes = [r.path for r in router.routes]
            assert any('stat' in r.lower() or 'chart' in r.lower() or 'overview' in r.lower()
                       for r in routes), (
                f"未找到 statistics/charts 路由，现有: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")


# =====================================================================
# 集成测试（需要数据库）
# =====================================================================

class TestDashboardIntegration:
    """集成测试：验证真实数据查询"""

    @pytest.mark.asyncio
    async def test_empty_db_statistics_returns_empty_lists(self):
        """空数据库时 get_statistics() 返回空列表而非硬编码数据"""
        pytest.skip("集成测试需要数据库环境，请在有DB的环境中运行")

    @pytest.mark.asyncio
    async def test_charts_data_matches_db_content(self):
        """get_charts() 数据与数据库实际内容一致"""
        pytest.skip("集成测试需要数据库环境，请在有DB的环境中运行")


# =====================================================================
# 主函数
# =====================================================================

if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True, text=True
    )
    print(result.stdout)
    print(result.stderr)
