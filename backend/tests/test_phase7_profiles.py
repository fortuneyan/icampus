"""
Phase 7 Tests - Student/Teacher Profiles and Audit Logs
"""

import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.models.student_profile import StudentProfile
from app.models.teacher_profile import TeacherProfile
from app.models.operation_log import OperationLog
from app.models.login_log import LoginLog
from app.models.data_access_log import DataAccessLog


class TestStudentProfileModel:
    """学生扩展信息模型测试"""

    def test_student_profile_creation(self):
        """测试创建学生扩展信息"""
        profile = StudentProfile(
            user_id=uuid4(),
            student_no="2024001",
            guardian_name="张三",
            guardian_phone="13800138000",
            is_left_behind=True,
            is_poor=False,
        )
        assert profile.student_no == "2024001"
        assert profile.guardian_name == "张三"
        assert profile.is_left_behind is True

    def test_student_profile_fields(self):
        """测试学生扩展信息字段"""
        profile = StudentProfile(
            user_id=uuid4(),
            student_no="2024002",
            enrollment_date=datetime.now(),
            student_status="active",
            province="北京市",
            city="北京市",
            district="朝阳区",
            address="某街道某号",
            is_disabled=False,
            is_orphan=False,
        )
        assert profile.student_status == "active"
        assert profile.province == "北京市"


class TestTeacherProfileModel:
    """教师扩展信息模型测试"""

    def test_teacher_profile_creation(self):
        """测试创建教师扩展信息"""
        profile = TeacherProfile(
            user_id=uuid4(),
            employee_no="T001",
            position="数学教师",
            title="高级教师",
            subject="数学",
            employment_type="full_time",
        )
        assert profile.employee_no == "T001"
        assert profile.position == "数学教师"
        assert profile.subject == "数学"

    def test_teacher_profile_fields(self):
        """测试教师扩展信息字段"""
        profile = TeacherProfile(
            user_id=uuid4(),
            employee_no="T002",
            hire_date=datetime.now(),
            education="本科",
            degree="学士",
            teacher_certificate="123456789",
            emergency_contact="李四",
            emergency_phone="13900139000",
        )
        assert profile.education == "本科"
        assert profile.degree == "学士"


class TestOperationLogModel:
    """操作日志模型测试"""

    def test_operation_log_creation(self):
        """测试创建操作日志"""
        log = OperationLog(
            user_id=uuid4(),
            username="admin",
            module="system",
            action="create",
            operation="创建用户",
            method="POST",
            path="/api/v1/system/users",
            ip_address="127.0.0.1",
            status_code=200,
            response_time=150,
        )
        assert log.module == "system"
        assert log.action == "create"
        assert log.status_code == 200

    def test_operation_log_error(self):
        """测试错误日志"""
        log = OperationLog(
            user_id=uuid4(),
            username="admin",
            module="system",
            action="delete",
            error_message="权限不足",
            status_code=403,
        )
        assert log.error_message == "权限不足"
        assert log.status_code == 403


class TestLoginLogModel:
    """登录日志模型测试"""

    def test_login_log_success(self):
        """测试成功登录日志"""
        log = LoginLog(
            user_id=uuid4(),
            username="admin",
            login_type="password",
            ip_address="192.168.1.100",
            device="Windows",
            browser="Chrome",
            status="success",
        )
        assert log.status == "success"
        assert log.login_type == "password"

    def test_login_log_failed(self):
        """测试失败登录日志"""
        log = LoginLog(
            username="admin",
            login_type="password",
            ip_address="192.168.1.100",
            status="failed",
            fail_reason="密码错误",
        )
        assert log.status == "failed"
        assert log.fail_reason == "密码错误"


class TestDataAccessLogModel:
    """数据访问日志模型测试"""

    def test_data_access_log_creation(self):
        """测试创建数据访问日志"""
        log = DataAccessLog(
            user_id=uuid4(),
            username="admin",
            resource_type="student",
            resource_id=uuid4(),
            resource_name="学生张三",
            data_level="L3",
            operation="read",
            status="success",
        )
        assert log.data_level == "L3"
        assert log.operation == "read"

    def test_data_access_log_l4(self):
        """测试L4级别数据访问"""
        log = DataAccessLog(
            user_id=uuid4(),
            username="admin",
            resource_type="student_profile",
            resource_id=uuid4(),
            data_level="L4",
            operation="export",
            status="success",
        )
        assert log.data_level == "L4"
        assert log.operation == "export"


class TestProfileSchemas:
    """扩展信息 Schema 测试"""

    def test_student_profile_create_schema(self):
        """测试学生扩展信息创建Schema"""
        from app.api.v1.edu.student_profiles import StudentProfileCreate

        data = StudentProfileCreate(
            user_id=uuid4(),
            student_no="2024003",
            guardian_name="王五",
            guardian_phone="13800138001",
        )
        assert data.student_no == "2024003"
        assert data.guardian_name == "王五"

    def test_teacher_profile_create_schema(self):
        """测试教师扩展信息创建Schema"""
        from app.api.v1.system.teacher_profiles import TeacherProfileCreate

        data = TeacherProfileCreate(
            user_id=uuid4(), employee_no="T003", position="英语教师", subject="英语"
        )
        assert data.employee_no == "T003"
        assert data.subject == "英语"
