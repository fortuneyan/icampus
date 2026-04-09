"""
第五阶段测试 - 统计报表与系统设置
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.dashboard import OverviewResponse, QuickAction
from app.schemas.report import ReportQuery, StudentReport, CustomReportCreate
from app.schemas.settings import SettingUpdate, LogQuery
from app.schemas.message import MessageCreate, UnreadCount


class TestDashboardSchemas:
    """仪表盘 Schemas 测试"""

    def test_overview_response_valid(self):
        """测试概览响应"""
        overview = OverviewResponse(
            student_count=100,
            teacher_count=20,
            class_count=10,
            course_count=50,
            resource_count=200,
        )
        assert overview.student_count == 100
        assert overview.teacher_count == 20

    def test_quick_action_valid(self):
        """测试快捷操作"""
        action = QuickAction(
            id="1", name="添加学生", icon="UserPlus", path="/edu/students"
        )
        assert action.name == "添加学生"
        assert action.path == "/edu/students"


class TestReportSchemas:
    """报表 Schemas 测试"""

    def test_report_query_valid(self):
        """测试报表查询"""
        query = ReportQuery(start_date="2024-01-01", end_date="2024-12-31")
        assert query.start_date == "2024-01-01"

    def test_custom_report_create_valid(self):
        """测试自定义报表创建"""
        report = CustomReportCreate(
            name="成绩报表", report_type="score", config={"type": "pie"}
        )
        assert report.name == "成绩报表"


class TestSettingsSchemas:
    """设置 Schemas 测试"""

    def test_setting_update_valid(self):
        """测试设置更新"""
        setting = SettingUpdate(
            setting_key="site_name", setting_value="智慧校园", value_type="string"
        )
        assert setting.setting_key == "site_name"

    def test_log_query_valid(self):
        """测试日志查询"""
        query = LogQuery(level="INFO", page=1, page_size=20)
        assert query.level == "INFO"


class TestMessageSchemas:
    """消息 Schemas 测试"""

    def test_message_create_valid(self):
        """测试消息创建"""
        from uuid import uuid4
        from datetime import datetime

        msg = MessageCreate(
            user_id=uuid4(), title="测试消息", content="内容", msg_type="system"
        )
        assert msg.title == "测试消息"

    def test_unread_count_valid(self):
        """测试未读数量"""
        count = UnreadCount(total=5, system=3, notice=2, task=0)
        assert count.total == 5


class TestModels:
    """数据模型测试"""

    def test_dashboard_model_exists(self):
        from app.models.dashboard import ReportConfig, SystemSetting, Message

        assert ReportConfig.__tablename__ == "report_configs"
        assert SystemSetting.__tablename__ == "system_settings"
        assert Message.__tablename__ == "messages"


class TestServices:
    """服务层测试"""

    def test_dashboard_service_can_be_instantiated(self):
        from unittest.mock import MagicMock
        from app.services.dashboard_service import DashboardService

        service = DashboardService(MagicMock())
        assert service is not None

    def test_report_service_can_be_instantiated(self):
        from unittest.mock import MagicMock
        from app.services.report_service import ReportService

        service = ReportService(MagicMock())
        assert service is not None

    def test_settings_service_can_be_instantiated(self):
        from unittest.mock import MagicMock
        from app.services.settings_service import SettingsService

        service = SettingsService(MagicMock())
        assert service is not None

    def test_message_service_can_be_instantiated(self):
        from unittest.mock import MagicMock
        from app.services.message_service import MessageService

        service = MessageService(MagicMock())
        assert service is not None


class TestAPIEndpoints:
    """API接口结构测试"""

    def test_dashboard_router_exists(self):
        from app.api.v1.dashboard import router

        assert router is not None

    def test_report_router_exists(self):
        from app.api.v1.report import router

        assert router is not None

    def test_settings_router_exists(self):
        from app.api.v1.settings import router

        assert router is not None

    def test_message_router_exists(self):
        from app.api.v1.message import router

        assert router is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
