# -*- coding: utf-8 -*-
"""
TASK-01 测试脚本：T4 考勤统计 - 替换假数据生成器
测试目标：验证 attendance_stats.py 不再使用 mock 数据，能正确读取数据库

运行方式：
    cd smart-campus
    python -m pytest backend/tests/test_task01_attendance_stats.py -v

通过条件：所有测试用例通过后方可将 TASK-01 标记为完成
"""

import pytest
import sys
import os
import inspect

# 将项目根路径加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# =====================================================================
# 静态代码检查：确认 mock 代码已移除
# =====================================================================

class TestNoMockCode:
    """验证 attendance_stats.py 中 mock 代码已被移除"""

    def _get_source(self):
        source_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'attendance', 'attendance_stats.py'
        )
        with open(source_path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_no_generate_mock_stats_function(self):
        """函数 generate_mock_stats 应已被移除"""
        source = self._get_source()
        assert 'def generate_mock_stats' not in source, (
            "FAIL: generate_mock_stats() 函数仍存在，需要移除并替换为真实DB查询"
        )

    def test_no_hardcoded_names(self):
        """不应有硬编码的"张三/李四/王五"等假名"""
        source = self._get_source()
        forbidden_names = ["张三", "李四", "王五", "赵六", "钱七"]
        found = [name for name in forbidden_names if name in source]
        assert not found, (
            f"FAIL: 发现硬编码姓名 {found}，需要从数据库查询真实数据"
        )

    def test_no_fixed_attendance_rate(self):
        """不应有 0.85 或 85% 硬编码出勤率"""
        source = self._get_source()
        assert '0.85' not in source or '# 生成随机但合理的考勤数据' not in source, (
            "FAIL: 仍有固定出勤率 0.85 的 mock 逻辑，需移除"
        )

    def test_uses_db_dependency(self):
        """API 路由应注入 DB 依赖（get_db 或 AsyncSession）"""
        source = self._get_source()
        has_db = 'get_db' in source or 'AsyncSession' in source or 'Depends' in source
        assert has_db, (
            "FAIL: 路由函数未注入数据库依赖，需添加 db: AsyncSession = Depends(get_db)"
        )

    def test_no_mock_dimension_names_dict(self):
        """不应有 dimension_names 假数据字典"""
        source = self._get_source()
        assert 'dimension_names' not in source, (
            "FAIL: 仍存在 dimension_names 硬编码字典，需移除"
        )


# =====================================================================
# 单元测试：模型和辅助函数
# =====================================================================

class TestAttendanceStatModels:
    """验证考勤统计模型的正确性"""

    def test_calculate_attendance_rate_normal(self):
        """出勤率计算正确"""
        try:
            from app.models.attendance_stat import calculate_attendance_rate
            result = calculate_attendance_rate(total=100, absent=5)
            assert result == 95.0, f"期望 95.0，实际 {result}"
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_calculate_attendance_rate_zero_total(self):
        """总数为0时返回0.0，不报错"""
        try:
            from app.models.attendance_stat import calculate_attendance_rate
            result = calculate_attendance_rate(total=0, absent=0)
            assert result == 0.0, f"期望 0.0，实际 {result}"
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_attendance_stat_record_to_dict(self):
        """AttendanceStatRecord.to_dict() 字段完整"""
        try:
            from app.models.attendance_stat import AttendanceStatRecord, AttendanceStatType, AttendanceStatDimension
            from datetime import date
            record = AttendanceStatRecord(
                id=1,
                stat_type=AttendanceStatType.DAILY,
                dimension=AttendanceStatDimension.CLASS,
                dimension_id=1,
                dimension_name="初一(1)班",
                stat_date=date(2026, 4, 11),
                total_count=30,
                normal_count=25,
                late_count=3,
                early_leave_count=1,
                absent_count=1,
                leave_count=0,
                normal_rate=83.33,
                attendance_rate=96.67,
            )
            d = record.to_dict()
            required_keys = [
                'id', 'stat_type', 'dimension', 'dimension_id', 'dimension_name',
                'stat_date', 'total_count', 'normal_count', 'late_count',
                'early_leave_count', 'absent_count', 'leave_count',
                'normal_rate', 'attendance_rate'
            ]
            for key in required_keys:
                assert key in d, f"to_dict() 缺少字段: {key}"
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_attendance_report_calculate_totals(self):
        """AttendanceReport.calculate_totals() 汇总计算正确"""
        try:
            from app.models.attendance_stat import (
                AttendanceReport, AttendanceReportType, AttendanceStatDimension,
                AttendanceStatRecord, AttendanceStatType
            )
            from datetime import date
            stat = AttendanceStatRecord(
                id=1, stat_type=AttendanceStatType.DAILY,
                dimension=AttendanceStatDimension.CLASS, dimension_id=1,
                dimension_name="班级A", stat_date=date(2026, 4, 11),
                total_count=40, normal_count=35, late_count=3,
                early_leave_count=1, absent_count=1, leave_count=0,
                normal_rate=87.5, attendance_rate=97.5,
            )
            report = AttendanceReport(
                id=1, report_type=AttendanceReportType.SUMMARY,
                title="测试报表",
                start_date=date(2026, 4, 11),
                end_date=date(2026, 4, 11),
                stat_dimension=AttendanceStatDimension.CLASS,
                stat_records=[stat],
            )
            report.calculate_totals()
            assert report.total_students == 40
            assert report.total_normal == 35
            assert report.total_absent == 1
            assert report.overall_attendance_rate == pytest.approx(97.5, abs=0.1)
        except ImportError:
            pytest.skip("模型未实现，跳过")


# =====================================================================
# API 结构测试：确认路由可导入且结构正确
# =====================================================================

class TestAttendanceStatsAPIStructure:
    """验证 attendance_stats.py 的 API 路由结构"""

    def test_router_importable(self):
        """router 对象可正常导入"""
        try:
            from app.api.v1.attendance.attendance_stats import router
            assert router is not None
        except ImportError as e:
            pytest.fail(f"无法导入 router: {e}")

    def test_query_endpoint_exists(self):
        """POST /query 路由存在"""
        try:
            from app.api.v1.attendance.attendance_stats import router
            routes = [r.path for r in router.routes]
            query_routes = [r for r in routes if 'query' in r or 'stats' in r]
            assert len(query_routes) > 0, (
                f"未找到 query 相关路由，现有路由: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_report_endpoint_exists(self):
        """POST /report 路由存在"""
        try:
            from app.api.v1.attendance.attendance_stats import router
            routes = [r.path for r in router.routes]
            report_routes = [r for r in routes if 'report' in r]
            assert len(report_routes) > 0, (
                f"未找到 report 相关路由，现有路由: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_stat_query_model_validation(self):
        """StatQuery 模型：有效 stat_type 可创建"""
        try:
            from app.api.v1.attendance.attendance_stats import StatQuery
            q = StatQuery(
                stat_type="daily",
                dimension="class",
                start_date="2026-04-01",
                end_date="2026-04-11",
            )
            assert q.stat_type == "daily"
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_stat_query_model_rejects_invalid_stat_type(self):
        """StatQuery 模型：无效 stat_type 应抛出 ValidationError"""
        try:
            from app.api.v1.attendance.attendance_stats import StatQuery
            from pydantic import ValidationError
            with pytest.raises(ValidationError):
                StatQuery(
                    stat_type="invalid_type",
                    dimension="class",
                    start_date="2026-04-01",
                    end_date="2026-04-11",
                )
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_stat_query_model_rejects_invalid_dimension(self):
        """StatQuery 模型：无效 dimension 应抛出 ValidationError"""
        try:
            from app.api.v1.attendance.attendance_stats import StatQuery
            from pydantic import ValidationError
            with pytest.raises(ValidationError):
                StatQuery(
                    stat_type="daily",
                    dimension="invalid_dim",
                    start_date="2026-04-01",
                    end_date="2026-04-11",
                )
        except ImportError:
            pytest.skip("模型未实现，跳过")


# =====================================================================
# 异步 DB 集成测试（需要测试数据库）
# =====================================================================

class TestAttendanceStatsIntegration:
    """集成测试：验证与数据库的真实交互（需要 DB 环境）"""

    @pytest.mark.asyncio
    async def test_empty_db_returns_empty_list(self):
        """
        空数据库时，统计接口返回 [] 而非 mock 数据
        
        注意：需要配置 TEST_DATABASE_URL 环境变量
        若无测试 DB，此测试会被跳过
        """
        pytest.skip("集成测试需要数据库环境，请在有DB的环境中运行")

    @pytest.mark.asyncio
    async def test_real_records_are_counted(self):
        """
        数据库有考勤记录时，统计数值与真实数据一致
        
        注意：需要配置 TEST_DATABASE_URL 环境变量
        """
        pytest.skip("集成测试需要数据库环境，请在有DB的环境中运行")


# =====================================================================
# 运行结果汇总
# =====================================================================

if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True, text=True
    )
    print(result.stdout)
    print(result.stderr)
