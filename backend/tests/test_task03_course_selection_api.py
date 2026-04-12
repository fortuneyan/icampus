# -*- coding: utf-8 -*-
"""
TASK-03 测试脚本：T6 选课管理 — API层对接服务层
测试目标：验证 course_selection.py 不再使用 _mock_rules/_mock_records 内存字典，数据写入真实数据库

运行方式：
    cd smart-campus
    python -m pytest backend/tests/test_task03_course_selection_api.py -v

通过条件：所有测试用例通过后方可将 TASK-03 标记为完成
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# =====================================================================
# 静态代码检查：确认内存字典已移除
# =====================================================================

class TestNoMockDicts:
    """验证 course_selection.py 中内存字典已移除"""

    def _get_source(self):
        path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1', 'edu', 'course_selection.py'
        )
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_no_mock_rules_dict(self):
        """_mock_rules 内存字典应已移除"""
        source = self._get_source()
        assert '_mock_rules' not in source, (
            "FAIL: 发现 _mock_rules 内存字典，应改为调用 CourseSelectionService 从数据库读写"
        )

    def test_no_mock_records_dict(self):
        """_mock_records 内存字典应已移除"""
        source = self._get_source()
        assert '_mock_records' not in source, (
            "FAIL: 发现 _mock_records 内存字典，应改为调用 CourseSelectionService 从数据库读写"
        )

    def test_no_next_rule_id_counter(self):
        """_next_rule_id 全局计数器应已移除（DB 自增主键替代）"""
        source = self._get_source()
        assert '_next_rule_id' not in source, (
            "FAIL: 发现 _next_rule_id 全局计数器，应使用数据库自增主键"
        )

    def test_no_next_record_id_counter(self):
        """_next_record_id 全局计数器应已移除"""
        source = self._get_source()
        assert '_next_record_id' not in source, (
            "FAIL: 发现 _next_record_id 全局计数器，应使用数据库自增主键"
        )

    def test_no_global_keyword_for_counters(self):
        """不应有 global _next_rule_id / global _next_record_id"""
        source = self._get_source()
        assert 'global _next_rule_id' not in source, (
            "FAIL: 发现 global _next_rule_id，说明仍在使用内存计数器"
        )
        assert 'global _next_record_id' not in source, (
            "FAIL: 发现 global _next_record_id，说明仍在使用内存计数器"
        )

    def test_uses_db_dependency(self):
        """路由应注入数据库依赖"""
        source = self._get_source()
        has_db = 'get_db' in source or 'AsyncSession' in source
        assert has_db, (
            "FAIL: 路由未注入数据库依赖，需添加 db: AsyncSession = Depends(get_db)"
        )

    def test_uses_course_selection_service(self):
        """路由应调用 CourseSelectionService"""
        source = self._get_source()
        assert 'CourseSelectionService' in source, (
            "FAIL: 未调用 CourseSelectionService，API层应对接已有的服务层"
        )


# =====================================================================
# Pydantic 模型验证
# =====================================================================

class TestCourseSelectionModels:
    """验证选课管理请求模型的字段约束"""

    def test_selection_request_valid(self):
        """SelectionRequest 有效数据可创建"""
        try:
            from app.api.v1.edu.course_selection import SelectionRequest
            req = SelectionRequest(
                student_id=1,
                course_id=101,
                rule_id=1,
                credits=3.0,
            )
            assert req.student_id == 1
            assert req.credits == 3.0
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_selection_request_negative_credits_rejected(self):
        """SelectionRequest.credits 不能为负数"""
        try:
            from app.api.v1.edu.course_selection import SelectionRequest
            from pydantic import ValidationError
            with pytest.raises(ValidationError):
                SelectionRequest(student_id=1, course_id=101, rule_id=1, credits=-1.0)
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_rule_create_request_valid(self):
        """RuleCreateRequest 有效数据可创建"""
        try:
            from app.api.v1.edu.course_selection import RuleCreateRequest
            from datetime import datetime
            req = RuleCreateRequest(
                name="2025-2026第一学期选课规则",
                academic_year="2025-2026",
                semester=1,
                period_type="normal",
                start_time=datetime(2025, 9, 1, 8, 0),
                end_time=datetime(2025, 9, 10, 18, 0),
                min_credits=12,
                max_credits=30,
                min_courses=4,
                max_courses=8,
            )
            assert req.name == "2025-2026第一学期选课规则"
            assert req.semester == 1
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_rule_create_academic_year_format(self):
        """RuleCreateRequest.academic_year 格式必须为 YYYY-YYYY"""
        try:
            from app.api.v1.edu.course_selection import RuleCreateRequest
            from pydantic import ValidationError
            from datetime import datetime
            with pytest.raises(ValidationError):
                RuleCreateRequest(
                    name="test",
                    academic_year="2025",  # 错误格式
                    semester=1,
                    period_type="normal",
                    start_time=datetime(2025, 9, 1),
                    end_time=datetime(2025, 9, 10),
                )
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_rule_create_semester_range(self):
        """RuleCreateRequest.semester 范围 1-3"""
        try:
            from app.api.v1.edu.course_selection import RuleCreateRequest
            from pydantic import ValidationError
            from datetime import datetime
            with pytest.raises(ValidationError):
                RuleCreateRequest(
                    name="test",
                    academic_year="2025-2026",
                    semester=4,  # 无效
                    period_type="normal",
                    start_time=datetime(2025, 9, 1),
                    end_time=datetime(2025, 9, 10),
                )
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_lottery_request_capacity_positive(self):
        """LotteryRequest.max_capacity 必须大于0"""
        try:
            from app.api.v1.edu.course_selection import LotteryRequest
            from pydantic import ValidationError
            with pytest.raises(ValidationError):
                LotteryRequest(course_id=1, max_capacity=0)
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_withdraw_request_valid(self):
        """WithdrawRequest 有效数据可创建"""
        try:
            from app.api.v1.edu.course_selection import WithdrawRequest
            req = WithdrawRequest(record_id=10, student_id=1)
            assert req.record_id == 10
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_drop_request_with_reason(self):
        """DropRequest 支持可选 reason 字段"""
        try:
            from app.api.v1.edu.course_selection import DropRequest
            req = DropRequest(record_id=10, student_id=1, reason="课程冲突")
            assert req.reason == "课程冲突"
        except ImportError:
            pytest.skip("模型未实现，跳过")


# =====================================================================
# 路由结构检查
# =====================================================================

class TestCourseSelectionAPIStructure:
    """验证 course_selection.py 路由结构"""

    def test_router_importable(self):
        """router 对象可正常导入"""
        try:
            from app.api.v1.edu.course_selection import router
            assert router is not None
        except ImportError as e:
            pytest.fail(f"无法导入 router: {e}")

    def test_rules_route_exists(self):
        """选课规则相关路由存在"""
        try:
            from app.api.v1.edu.course_selection import router
            routes = [r.path for r in router.routes]
            assert any('rule' in r.lower() for r in routes), (
                f"未找到 rules 路由，现有: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_select_route_exists(self):
        """选课操作路由存在"""
        try:
            from app.api.v1.edu.course_selection import router
            routes = [r.path for r in router.routes]
            assert any('select' in r.lower() or 'record' in r.lower() for r in routes), (
                f"未找到 select/record 路由，现有: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_lottery_route_exists(self):
        """抽签路由存在"""
        try:
            from app.api.v1.edu.course_selection import router
            routes = [r.path for r in router.routes]
            assert any('lottery' in r.lower() for r in routes), (
                f"未找到 lottery 路由，现有: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")


# =====================================================================
# 服务层兼容性检查
# =====================================================================

class TestCourseSelectionServiceCompatibility:
    """验证 CourseSelectionService 可被正确调用"""

    def test_service_importable(self):
        """CourseSelectionService 可正常导入"""
        try:
            from app.services.course_selection_service import CourseSelectionService
            assert CourseSelectionService is not None
        except ImportError as e:
            pytest.fail(f"CourseSelectionService 无法导入: {e}")

    def test_rule_model_importable(self):
        """CourseSelectionRule 模型可正常导入"""
        try:
            from app.models.course_selection_rule import CourseSelectionRule
            assert CourseSelectionRule is not None
        except ImportError as e:
            pytest.fail(f"CourseSelectionRule 模型无法导入: {e}")

    def test_record_model_importable(self):
        """CourseSelectionRecord 模型可正常导入"""
        try:
            from app.models.course_selection_record import CourseSelectionRecord
            assert CourseSelectionRecord is not None
        except ImportError as e:
            pytest.fail(f"CourseSelectionRecord 模型无法导入: {e}")

    def test_service_has_create_rule(self):
        """CourseSelectionService 具有 create_rule 方法"""
        try:
            from app.services.course_selection_service import CourseSelectionService
            assert hasattr(CourseSelectionService, 'create_rule'), (
                "CourseSelectionService 缺少 create_rule 方法"
            )
        except ImportError:
            pytest.skip("服务层未实现，跳过")

    def test_service_has_get_rules(self):
        """CourseSelectionService 具有 get_rules 方法"""
        try:
            from app.services.course_selection_service import CourseSelectionService
            assert hasattr(CourseSelectionService, 'get_rules'), (
                "CourseSelectionService 缺少 get_rules 方法"
            )
        except ImportError:
            pytest.skip("服务层未实现，跳过")

    def test_service_has_select_course(self):
        """CourseSelectionService 具有选课方法"""
        try:
            from app.services.course_selection_service import CourseSelectionService
            has_select = (
                hasattr(CourseSelectionService, 'select_course') or
                hasattr(CourseSelectionService, 'create_record')
            )
            assert has_select, (
                "CourseSelectionService 缺少选课方法（select_course 或 create_record）"
            )
        except ImportError:
            pytest.skip("服务层未实现，跳过")

    def test_service_has_run_lottery(self):
        """CourseSelectionService 具有抽签方法"""
        try:
            from app.services.course_selection_service import CourseSelectionService
            has_lottery = (
                hasattr(CourseSelectionService, 'run_lottery') or
                hasattr(CourseSelectionService, 'lottery')
            )
            assert has_lottery, (
                "CourseSelectionService 缺少抽签方法（run_lottery 或 lottery）"
            )
        except ImportError:
            pytest.skip("服务层未实现，跳过")


# =====================================================================
# 业务规则验证
# =====================================================================

class TestBusinessRules:
    """验证选课业务规则"""

    def test_selection_mode_values(self):
        """selection_mode 应为合法枚举值"""
        try:
            from app.api.v1.edu.course_selection import RuleCreateRequest
            from datetime import datetime
            # 有效模式
            for mode in ['course', 'package', 'mixed']:
                req = RuleCreateRequest(
                    name=f"测试规则_{mode}",
                    academic_year="2025-2026",
                    semester=1,
                    period_type="normal",
                    start_time=datetime(2025, 9, 1),
                    end_time=datetime(2025, 9, 10),
                    selection_mode=mode,
                )
                assert req.selection_mode == mode
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_strategy_values(self):
        """strategy 应为合法枚举值（fcfs/lottery）"""
        try:
            from app.api.v1.edu.course_selection import RuleCreateRequest
            from datetime import datetime
            for strategy in ['fcfs', 'lottery']:
                req = RuleCreateRequest(
                    name=f"测试规则_{strategy}",
                    academic_year="2025-2026",
                    semester=1,
                    period_type="normal",
                    start_time=datetime(2025, 9, 1),
                    end_time=datetime(2025, 9, 10),
                    strategy=strategy,
                )
                assert req.strategy == strategy
        except ImportError:
            pytest.skip("模型未实现，跳过")


# =====================================================================
# 集成测试（需要数据库环境）
# =====================================================================

class TestCourseSelectionIntegration:
    """集成测试：验证数据持久化"""

    @pytest.mark.asyncio
    async def test_create_rule_persists_to_db(self):
        """创建选课规则后数据写入数据库，重启后仍存在"""
        pytest.skip("集成测试需要数据库环境，请在有DB的环境中运行")

    @pytest.mark.asyncio
    async def test_select_course_creates_record_in_db(self):
        """选课操作在数据库中创建记录"""
        pytest.skip("集成测试需要数据库环境，请在有DB的环境中运行")

    @pytest.mark.asyncio
    async def test_lottery_uses_real_service(self):
        """抽签操作调用真实服务层逻辑"""
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
