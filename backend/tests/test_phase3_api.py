"""
第三阶段 API 测试 - 教务管理模块
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app


@pytest_asyncio.fixture
async def client():
    """创建测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestEducationAPI:
    """教务管理API测试"""

    @pytest.mark.asyncio
    async def test_get_students_missing_auth(self, client):
        """测试无认证获取学生列表"""
        response = await client.get("/api/v1/edu/students")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_grades_missing_auth(self, client):
        """测试无认证获取年级列表"""
        response = await client.get("/api/v1/edu/grades")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_classes_missing_auth(self, client):
        """测试无认证获取班级列表"""
        response = await client.get("/api/v1/edu/classes")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_courses_missing_auth(self, client):
        """测试无认证获取课程列表"""
        response = await client.get("/api/v1/edu/courses")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_scores_missing_auth(self, client):
        """测试无认证获取成绩列表"""
        response = await client.get("/api/v1/edu/scores")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_schedules_missing_auth(self, client):
        """测试无认证获取排课列表"""
        response = await client.get("/api/v1/edu/schedules")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_create_student_missing_auth(self, client):
        """测试无认证创建学生"""
        response = await client.post(
            "/api/v1/edu/students", json={"student_no": "2024001", "name": "张三"}
        )
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_create_grade_missing_auth(self, client):
        """测试无认证创建年级"""
        response = await client.post(
            "/api/v1/edu/grades",
            json={"name": "2024级", "year": 2024, "grade_level": 1},
        )
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_create_class_missing_auth(self, client):
        """测试无认证创建班级"""
        response = await client.post(
            "/api/v1/edu/classes", json={"name": "一年级一班", "class_no": 1}
        )
        assert response.status_code in [401, 403]


class TestAPIResponseFormat:
    """API响应格式测试"""

    @pytest.mark.asyncio
    async def test_root_response_format(self, client):
        """测试根路径响应格式"""
        response = await client.get("/")
        data = response.json()
        assert "message" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_health_check_response(self, client):
        """测试健康检查响应"""
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
