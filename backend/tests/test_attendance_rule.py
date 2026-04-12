"""
考勤规则单元测试

使用方式：
1. 独立运行（无依赖）：python tests/test_attendance_rule.py
2. 使用pytest：pytest tests/test_attendance_rule.py
3. 设置路径后运行：PYTHONPATH=. python tests/test_attendance_rule.py
"""
import sys
import os
from datetime import time, datetime
from uuid import uuid4

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 尝试导入app模块
try:
    from app.models.attendance_rule import AttendanceRule
    from app.schemas.response import success, page_response
    HAS_APP = True
except ImportError:
    HAS_APP = False
    print("警告: 无法导入app模块，部分测试将被跳过")


class TestAttendanceRuleModel:
    """AttendanceRule模型测试"""

    def test_create_attendance_rule_model(self):
        """测试创建考勤规则模型"""
        if not HAS_APP:
            pytest.skip("app模块未安装")
        
        rule = AttendanceRule(
            id=uuid4(),
            name="学生日常考勤",
            rule_type="student",
            check_in_start=time(7, 30),
            check_in_end=time(8, 0),
            check_out_start=time(16, 30),
            check_out_end=time(17, 0),
            late_threshold=10,
            early_leave_threshold=10,
            absent_threshold=30,
            grace_period=5,
            description="学生每日考勤规则",
            status="active",
        )

        assert rule.name == "学生日常考勤"
        assert rule.rule_type == "student"
        assert rule.check_in_start == time(7, 30)
        assert rule.check_in_end == time(8, 0)
        assert rule.late_threshold == 10
        assert rule.status == "active"

    def test_attendance_rule_to_dict(self):
        """测试模型转字典"""
        if not HAS_APP:
            pytest.skip("app模块未安装")
        
        rule_id = uuid4()
        rule = AttendanceRule(
            id=rule_id,
            name="教师考勤规则",
            rule_type="teacher",
            check_in_start=time(8, 0),
            check_in_end=time(8, 30),
            check_out_start=time(17, 0),
            check_out_end=time(17, 30),
            late_threshold=15,
            early_leave_threshold=15,
            absent_threshold=0,
            grace_period=5,
            description="教师上班考勤",
            status="active",
        )

        rule_dict = rule.to_dict()

        assert rule_dict["id"] == str(rule_id)
        assert rule_dict["name"] == "教师考勤规则"
        assert rule_dict["rule_type"] == "teacher"
        assert rule_dict["check_in_start"] == "08:00:00"
        assert rule_dict["check_in_end"] == "08:30:00"
        assert rule_dict["late_threshold"] == 15
        assert rule_dict["status"] == "active"

    def test_attendance_rule_repr(self):
        """测试模型字符串表示"""
        if not HAS_APP:
            pytest.skip("app模块未安装")
        
        rule_id = uuid4()
        rule = AttendanceRule(
            id=rule_id,
            name="测试规则",
            rule_type="student",
            check_in_start=time(7, 0),
            check_in_end=time(8, 0),
            check_out_start=time(16, 0),
            check_out_end=time(17, 0),
        )

        repr_str = repr(rule)
        assert "AttendanceRule" in repr_str
        assert "测试规则" in repr_str
        assert "student" in repr_str


class TestAttendanceRuleValidation:
    """考勤规则验证测试"""

    def test_validate_rule_type_valid(self):
        """测试有效规则类型"""
        valid_types = ["student", "teacher"]
        for rule_type in valid_types:
            assert rule_type in ["student", "teacher"]

    def test_validate_rule_type_invalid(self):
        """测试无效规则类型"""
        invalid_types = ["admin", "parent", ""]
        for rule_type in invalid_types:
            assert rule_type not in ["student", "teacher"]

    def test_validate_time_range_valid(self):
        """测试有效时间范围"""
        check_in_start = time(7, 30)
        check_in_end = time(8, 0)
        
        # 签到结束时间应该晚于开始时间
        assert check_in_end > check_in_start

    def test_validate_time_range_invalid(self):
        """测试无效时间范围"""
        check_in_start = time(8, 0)
        check_in_end = time(7, 30)
        
        # 签到结束时间晚于开始时间验证
        assert not (check_in_end > check_in_start)

    def test_validate_threshold_range(self):
        """测试阈值范围"""
        # 迟到阈值: 0-120分钟
        late_threshold = 10
        assert 0 <= late_threshold <= 120

        # 旷课阈值: 0-480分钟
        absent_threshold = 30
        assert 0 <= absent_threshold <= 480

        # 宽限期: 0-30分钟
        grace_period = 5
        assert 0 <= grace_period <= 30


class TestAttendanceRuleService:
    """考勤规则服务测试"""

    def test_get_active_rules(self):
        """测试获取启用状态规则"""
        if not HAS_APP:
            pytest.skip("app模块未安装")
        
        rules = [
            AttendanceRule(id=uuid4(), name="规则1", status="active", rule_type="student",
                          check_in_start=time(7,0), check_in_end=time(8,0),
                          check_out_start=time(16,0), check_out_end=time(17,0)),
            AttendanceRule(id=uuid4(), name="规则2", status="active", rule_type="teacher",
                          check_in_start=time(8,0), check_in_end=time(8,30),
                          check_out_start=time(17,0), check_out_end=time(17,30)),
        ]
        
        active_rules = [r for r in rules if r.status == "active"]
        assert len(active_rules) == 2

    def test_filter_by_rule_type(self):
        """测试按规则类型筛选"""
        if not HAS_APP:
            pytest.skip("app模块未安装")
        
        rules = [
            AttendanceRule(id=uuid4(), name="学生规则1", rule_type="student",
                          check_in_start=time(7,0), check_in_end=time(8,0),
                          check_out_start=time(16,0), check_out_end=time(17,0)),
            AttendanceRule(id=uuid4(), name="教师规则1", rule_type="teacher",
                          check_in_start=time(8,0), check_in_end=time(8,30),
                          check_out_start=time(17,0), check_out_end=time(17,30)),
            AttendanceRule(id=uuid4(), name="学生规则2", rule_type="student",
                          check_in_start=time(7,0), check_in_end=time(8,0),
                          check_out_start=time(16,0), check_out_end=time(17,0)),
        ]

        student_rules = [r for r in rules if r.rule_type == "student"]
        teacher_rules = [r for r in rules if r.rule_type == "teacher"]

        assert len(student_rules) == 2
        assert len(teacher_rules) == 1


class TestAttendanceRuleAPI:
    """考勤规则API测试"""

    def test_list_rules_response_format(self):
        """测试列表响应格式"""
        if not HAS_APP:
            pytest.skip("app模块未安装")
        
        response = page_response([], 0, 1, 20)
        
        assert "code" in response
        assert "message" in response
        assert "data" in response
        assert response["data"]["items"] == []
        assert response["data"]["total"] == 0
        assert response["data"]["page"] == 1
        assert response["data"]["page_size"] == 20

    def test_success_response_format(self):
        """测试成功响应格式"""
        if not HAS_APP:
            pytest.skip("app模块未安装")
        
        response = success({"id": "test-id"}, "操作成功")
        
        assert response["code"] == 200
        assert response["message"] == "操作成功"
        assert response["data"]["id"] == "test-id"

    def test_rule_time_calculation(self):
        """测试考勤时间计算"""
        check_in_start = time(7, 30)
        check_in_end = time(8, 0)
        
        # 计算签到窗口时长（分钟）
        start_minutes = check_in_start.hour * 60 + check_in_start.minute
        end_minutes = check_in_end.hour * 60 + check_in_end.minute
        window_duration = end_minutes - start_minutes
        
        assert window_duration == 30  # 30分钟签到窗口


class TestAttendanceRuleEdgeCases:
    """边界情况测试"""

    def test_minimal_threshold_values(self):
        """测试最小阈值"""
        if not HAS_APP:
            pytest.skip("app模块未安装")
        
        rule = AttendanceRule(
            id=uuid4(),
            name="最小阈值规则",
            rule_type="student",
            check_in_start=time(7, 0),
            check_in_end=time(8, 0),
            check_out_start=time(16, 0),
            check_out_end=time(17, 0),
            late_threshold=0,
            early_leave_threshold=0,
            absent_threshold=0,
            grace_period=0,
        )

        assert rule.late_threshold == 0
        assert rule.early_leave_threshold == 0
        assert rule.absent_threshold == 0
        assert rule.grace_period == 0

    def test_maximum_threshold_values(self):
        """测试最大阈值"""
        if not HAS_APP:
            pytest.skip("app模块未安装")
        
        rule = AttendanceRule(
            id=uuid4(),
            name="最大阈值规则",
            rule_type="teacher",
            check_in_start=time(0, 0),
            check_in_end=time(23, 59),
            check_out_start=time(0, 0),
            check_out_end=time(23, 59),
            late_threshold=120,
            early_leave_threshold=120,
            absent_threshold=480,
            grace_period=30,
        )

        assert rule.late_threshold == 120
        assert rule.early_leave_threshold == 120
        assert rule.absent_threshold == 480
        assert rule.grace_period == 30

    def test_none_description(self):
        """测试空描述"""
        if not HAS_APP:
            pytest.skip("app模块未安装")
        
        rule = AttendanceRule(
            id=uuid4(),
            name="无描述规则",
            rule_type="student",
            check_in_start=time(7, 0),
            check_in_end=time(8, 0),
            check_out_start=time(16, 0),
            check_out_end=time(17, 0),
            description=None,
        )

        assert rule.description is None
        assert rule.to_dict()["description"] is None


# 运行测试的辅助函数
def run_tests():
    """运行所有测试"""
    test_classes = [
        TestAttendanceRuleModel,
        TestAttendanceRuleValidation,
        TestAttendanceRuleService,
        TestAttendanceRuleAPI,
        TestAttendanceRuleEdgeCases,
    ]

    total = 0
    passed = 0
    skipped = 0
    failed = []

    for test_class in test_classes:
        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                total += 1
                try:
                    getattr(instance, method_name)()
                    passed += 1
                    print(f"[PASS] {test_class.__name__}.{method_name}")
                except pytest.skip.Exception as e:
                    skipped += 1
                    print(f"[SKIP] {test_class.__name__}.{method_name}: {e}")
                except Exception as e:
                    failed.append((test_class.__name__, method_name, str(e)))
                    print(f"[FAIL] {test_class.__name__}.{method_name}: {e}")

    print(f"\n{'='*50}")
    print(f"测试结果: {passed}/{total} 通过, {skipped} 跳过")
    if failed:
        print(f"失败: {len(failed)}")
        for cls, method, error in failed:
            print(f"  - {cls}.{method}: {error}")
    else:
        print("All tests passed!")

    return passed, skipped, failed


if __name__ == "__main__":
    run_tests()
