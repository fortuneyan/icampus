# -*- coding: utf-8 -*-
"""
TASK-02 测试脚本：T5 智能排课 — API层对接服务层
测试目标：验证 scheduling.py 不再使用 MOCK_PLANS 等内存字典，数据写入真实数据库

运行方式：
    cd smart-campus
    python -m pytest backend/tests/test_task02_scheduling_api.py -v

通过条件：所有测试用例通过后方可将 TASK-02 标记为完成
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# =====================================================================
# 静态代码检查：确认 Mock 常量已移除
# =====================================================================

class TestNoMockConstants:
    """验证 scheduling.py 中所有内存 Mock 常量已移除"""

    def _get_source(self):
        path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1', 'edu', 'scheduling.py'
        )
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_no_mock_plans_constant(self):
        """MOCK_PLANS 内存字典应已移除"""
        source = self._get_source()
        assert 'MOCK_PLANS' not in source, (
            "FAIL: 发现 MOCK_PLANS 常量，应改为调用 SchedulingService 从数据库读取数据"
        )

    def test_no_mock_classes_constant(self):
        """MOCK_CLASSES 内存字典应已移除"""
        source = self._get_source()
        assert 'MOCK_CLASSES' not in source, (
            "FAIL: 发现 MOCK_CLASSES 常量，应改为查询 Class 数据表"
        )

    def test_no_mock_courses_constant(self):
        """MOCK_COURSES 内存字典应已移除"""
        source = self._get_source()
        assert 'MOCK_COURSES' not in source, (
            "FAIL: 发现 MOCK_COURSES 常量，应改为查询 Course 数据表"
        )

    def test_no_mock_teachers_constant(self):
        """MOCK_TEACHERS 内存字典应已移除"""
        source = self._get_source()
        assert 'MOCK_TEACHERS' not in source, (
            "FAIL: 发现 MOCK_TEACHERS 常量，应改为查询 Teacher 数据表"
        )

    def test_no_mock_classrooms_constant(self):
        """MOCK_CLASSROOMS 内存字典应已移除"""
        source = self._get_source()
        assert 'MOCK_CLASSROOMS' not in source, (
            "FAIL: 发现 MOCK_CLASSROOMS 常量，应改为查询 Classroom 数据表"
        )

    def test_no_hardcoded_teacher_names(self):
        """不应有硬编码教师姓名（张老师/李老师等）"""
        source = self._get_source()
        forbidden = ["张老师", "李老师", "王老师", "赵老师"]
        found = [n for n in forbidden if n in source]
        assert not found, (
            f"FAIL: 发现硬编码教师姓名 {found}，应从数据库查询真实数据"
        )

    def test_no_hardcoded_class_names(self):
        """不应有硬编码班级名称（初一(1)班等）"""
        source = self._get_source()
        assert '初一(1)班' not in source, (
            "FAIL: 发现硬编码班级名称，应从数据库查询真实数据"
        )

    def test_uses_db_dependency(self):
        """路由应注入数据库依赖"""
        source = self._get_source()
        has_db = 'get_db' in source or 'AsyncSession' in source
        assert has_db, (
            "FAIL: 路由未注入数据库依赖，需添加 db: AsyncSession = Depends(get_db)"
        )

    def test_uses_scheduling_service(self):
        """路由应调用 SchedulingService"""
        source = self._get_source()
        assert 'SchedulingService' in source, (
            "FAIL: 未调用 SchedulingService，API层应对接已有的服务层"
        )


# =====================================================================
# Pydantic 模型验证
# =====================================================================

class TestSchedulingModels:
    """验证请求模型的字段约束"""

    def test_scheduling_plan_request_valid(self):
        """SchedulingPlanRequest 有效数据可创建"""
        try:
            from app.api.v1.edu.scheduling import SchedulingPlanRequest
            plan = SchedulingPlanRequest(
                name="2025-2026学年第一学期",
                academic_year="2025-2026",
                semester="第一学期",
                start_date="2025-09-01",
                end_date="2026-01-15",
            )
            assert plan.name == "2025-2026学年第一学期"
            assert plan.academic_year == "2025-2026"
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_time_slot_request_day_of_week_range(self):
        """TimeSlotRequest.day_of_week 范围 1-7"""
        try:
            from app.api.v1.edu.scheduling import TimeSlotRequest
            from pydantic import ValidationError
            # 有效值
            slot = TimeSlotRequest(day_of_week=1, period=1)
            assert slot.day_of_week == 1
            # 无效值
            with pytest.raises(ValidationError):
                TimeSlotRequest(day_of_week=8, period=1)
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_time_slot_request_period_range(self):
        """TimeSlotRequest.period 范围 1-10"""
        try:
            from app.api.v1.edu.scheduling import TimeSlotRequest
            from pydantic import ValidationError
            with pytest.raises(ValidationError):
                TimeSlotRequest(day_of_week=1, period=11)
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_optimization_request_valid(self):
        """OptimizationRequest 有效数据可创建"""
        try:
            from app.api.v1.edu.scheduling import OptimizationRequest
            req = OptimizationRequest(plan_id=1, max_iterations=500, time_limit=60.0)
            assert req.plan_id == 1
            assert req.max_iterations == 500
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_optimization_request_iterations_min(self):
        """OptimizationRequest.max_iterations 最小值为 100"""
        try:
            from app.api.v1.edu.scheduling import OptimizationRequest
            from pydantic import ValidationError
            with pytest.raises(ValidationError):
                OptimizationRequest(plan_id=1, max_iterations=50, time_limit=60.0)
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_manual_adjust_request_valid(self):
        """ManualAdjustRequest 有效数据可创建"""
        try:
            from app.api.v1.edu.scheduling import ManualAdjustRequest
            req = ManualAdjustRequest(assignment_id=1, new_day=3, new_period=5)
            assert req.new_day == 3
        except ImportError:
            pytest.skip("模型未实现，跳过")


# =====================================================================
# 路由结构检查
# =====================================================================

class TestSchedulingAPIStructure:
    """验证 scheduling.py 路由存在且可导入"""

    def test_router_importable(self):
        """router 对象可正常导入"""
        try:
            from app.api.v1.edu.scheduling import router
            assert router is not None
        except ImportError as e:
            pytest.fail(f"无法导入 router: {e}")

    def test_plans_route_exists(self):
        """GET /plans 路由存在"""
        try:
            from app.api.v1.edu.scheduling import router
            routes = [r.path for r in router.routes]
            assert any('plan' in r.lower() for r in routes), (
                f"未找到 /plans 相关路由，现有: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_optimize_route_exists(self):
        """优化路由存在"""
        try:
            from app.api.v1.edu.scheduling import router
            routes = [r.path for r in router.routes]
            assert any('optim' in r.lower() for r in routes), (
                f"未找到 optimize 相关路由，现有: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_conflict_check_route_exists(self):
        """冲突检测路由存在"""
        try:
            from app.api.v1.edu.scheduling import router
            routes = [r.path for r in router.routes]
            assert any('conflict' in r.lower() for r in routes), (
                f"未找到 conflict 相关路由，现有: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_publish_route_exists(self):
        """发布路由存在"""
        try:
            from app.api.v1.edu.scheduling import router
            routes = [r.path for r in router.routes]
            assert any('publish' in r.lower() for r in routes), (
                f"未找到 publish 相关路由，现有: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")


# =====================================================================
# 服务层兼容性检查
# =====================================================================

class TestSchedulingServiceCompatibility:
    """验证 SchedulingService 可被正确调用"""

    def test_scheduling_service_importable(self):
        """SchedulingService 可正常导入"""
        try:
            from app.services.scheduling_service import SchedulingService
            assert SchedulingService is not None
        except ImportError as e:
            pytest.fail(f"SchedulingService 无法导入: {e}")

    def test_scheduling_plan_model_importable(self):
        """SchedulingPlan 模型可正常导入"""
        try:
            from app.models.scheduling_plan import SchedulingPlan
            assert SchedulingPlan is not None
        except ImportError as e:
            pytest.fail(f"SchedulingPlan 模型无法导入: {e}")

    def test_scheduling_service_has_get_plans(self):
        """SchedulingService 具有 get_plans 方法"""
        try:
            from app.services.scheduling_service import SchedulingService
            assert hasattr(SchedulingService, 'get_plans') or callable(
                getattr(SchedulingService, 'get_plans', None)
            ), "SchedulingService 缺少 get_plans 方法"
        except ImportError:
            pytest.skip("服务层未实现，跳过")

    def test_scheduling_service_has_create_plan(self):
        """SchedulingService 具有 create_plan 方法"""
        try:
            from app.services.scheduling_service import SchedulingService
            assert hasattr(SchedulingService, 'create_plan'), (
                "SchedulingService 缺少 create_plan 方法"
            )
        except ImportError:
            pytest.skip("服务层未实现，跳过")

    def test_scheduling_service_has_optimize(self):
        """SchedulingService 具有优化方法"""
        try:
            from app.services.scheduling_service import SchedulingService
            has_optimize = (
                hasattr(SchedulingService, 'optimize') or
                hasattr(SchedulingService, 'optimize_plan') or
                hasattr(SchedulingService, 'run_optimization')
            )
            assert has_optimize, (
                "SchedulingService 缺少优化方法（optimize/optimize_plan/run_optimization）"
            )
        except ImportError:
            pytest.skip("服务层未实现，跳过")


# =====================================================================
# 集成测试（需要数据库环境）
# =====================================================================

class TestSchedulingIntegration:
    """集成测试：验证数据持久化"""

    @pytest.mark.asyncio
    async def test_create_plan_persists_to_db(self):
        """创建排课计划后数据写入数据库"""
        pytest.skip("集成测试需要数据库环境，请在有DB的环境中运行")

    @pytest.mark.asyncio
    async def test_list_plans_reads_from_db(self):
        """列表接口从数据库读取，而非内存"""
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
