"""
第四阶段测试 - 资源与AI模块
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.resource import ResourceCreate, CategoryCreate
from app.schemas.ai import ChatRequest, SessionCreate
from app.schemas.exam import PaperCreate, QuestionCreate
from app.schemas.attendance import RuleCreate, CheckInRequest
from app.schemas.notice import NoticeCreate


class TestResourceSchemas:
    """资源 Schemas 测试"""

    def test_resource_create_valid(self):
        """测试资源创建"""
        resource = ResourceCreate(title="Python教程", resource_type="video")
        assert resource.title == "Python教程"
        assert resource.resource_type == "video"

    def test_category_create_valid(self):
        """测试分类创建"""
        category = CategoryCreate(name="视频课程")
        assert category.name == "视频课程"


class TestAISchemas:
    """AI Schemas 测试"""

    def test_chat_request_valid(self):
        """测试聊天请求"""
        request = ChatRequest(message="你好")
        assert request.message == "你好"

    def test_session_create_valid(self):
        """测试会话创建"""
        session = SessionCreate(title="新对话")
        assert session.title == "新对话"


class TestExamSchemas:
    """考试 Schemas 测试"""

    def test_paper_create_valid(self):
        """测试试卷创建"""
        paper = PaperCreate(title="期末考试", duration=120)
        assert paper.title == "期末考试"
        assert paper.duration == 120

    def test_question_create_valid(self):
        """测试题目创建"""
        question = QuestionCreate(content="什么是Python?", question_type="essay")
        assert question.content == "什么是Python?"
        assert question.question_type == "essay"


class TestAttendanceSchemas:
    """考勤 Schemas 测试"""

    def test_rule_create_valid(self):
        """测试考勤规则创建"""
        from datetime import time

        rule = RuleCreate(
            name="上班签到", check_in_start=time(9, 0), check_in_end=time(9, 30)
        )
        assert rule.name == "上班签到"
        assert rule.check_in_start.hour == 9


class TestNoticeSchemas:
    """通知 Schemas 测试"""

    def test_notice_create_valid(self):
        """测试通知创建"""
        notice = NoticeCreate(title="重要通知", notice_type="urgent")
        assert notice.title == "重要通知"
        assert notice.notice_type == "urgent"


class TestModels:
    """数据模型测试"""

    def test_resource_model_exists(self):
        from app.models.resource import Resource, ResourceCategory

        assert Resource.__tablename__ == "resources"
        assert ResourceCategory.__tablename__ == "resource_categories"

    def test_ai_model_exists(self):
        from app.models.ai_model import AISession, AIMessage

        assert AISession.__tablename__ == "ai_sessions"
        assert AIMessage.__tablename__ == "ai_messages"

    def test_exam_model_exists(self):
        from app.models.exam import ExamPaper, Question

        assert ExamPaper.__tablename__ == "exam_papers"
        assert Question.__tablename__ == "questions"

    def test_attendance_model_exists(self):
        from app.models.attendance import AttendanceRule, AttendanceRecord

        assert AttendanceRule.__tablename__ == "attendance_rules"
        assert AttendanceRecord.__tablename__ == "attendance_records"

    def test_notice_model_exists(self):
        from app.models.notice import Notice, NoticeRead

        assert Notice.__tablename__ == "notices"
        assert NoticeRead.__tablename__ == "notice_reads"


class TestServices:
    """服务层测试"""

    def test_resource_service_can_be_instantiated(self):
        from unittest.mock import MagicMock
        from app.services.resource_service import ResourceService

        service = ResourceService(MagicMock())
        assert service is not None

    def test_ai_service_can_be_instantiated(self):
        from unittest.mock import MagicMock
        from app.services.ai_service import AIService

        service = AIService(MagicMock())
        assert service is not None

    def test_exam_service_can_be_instantiated(self):
        from unittest.mock import MagicMock
        from app.services.exam_service import PaperService

        service = PaperService(MagicMock())
        assert service is not None

    def test_attendance_service_can_be_instantiated(self):
        from unittest.mock import MagicMock
        from app.services.attendance_service import RuleService

        service = RuleService(MagicMock())
        assert service is not None

    def test_notice_service_can_be_instantiated(self):
        from unittest.mock import MagicMock
        from app.services.notice_service import NoticeService

        service = NoticeService(MagicMock())
        assert service is not None


class TestAPIEndpoints:
    """API接口结构测试"""

    def test_resource_router_exists(self):
        from app.api.v1.resource import router

        assert router is not None

    def test_ai_router_exists(self):
        from app.api.v1.ai import router

        assert router is not None

    def test_exam_router_exists(self):
        from app.api.v1.exam import router

        assert router is not None

    def test_attendance_router_exists(self):
        from app.api.v1.attendance import router

        assert router is not None

    def test_notice_router_exists(self):
        from app.api.v1.notice import router

        assert router is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
