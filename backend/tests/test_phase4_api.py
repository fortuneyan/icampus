"""
第四阶段 API 测试 - 资源与AI模块
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
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestResourceAPI:
    """资源API测试"""

    @pytest.mark.asyncio
    async def test_get_resources_missing_auth(self, client):
        response = await client.get("/api/v1/resource/resources")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_categories_missing_auth(self, client):
        response = await client.get("/api/v1/resource/categories")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_create_resource_missing_auth(self, client):
        response = await client.post(
            "/api/v1/resource/resources", json={"title": "测试"}
        )
        assert response.status_code in [401, 403]


class TestAIAPI:
    """AI API测试"""

    @pytest.mark.asyncio
    async def test_chat_missing_auth(self, client):
        response = await client.post("/api/v1/ai/chat", json={"message": "你好"})
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_sessions_missing_auth(self, client):
        response = await client.get("/api/v1/ai/sessions")
        assert response.status_code in [401, 403]


class TestExamAPI:
    """考试API测试"""

    @pytest.mark.asyncio
    async def test_get_papers_missing_auth(self, client):
        response = await client.get("/api/v1/exam/papers")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_questions_missing_auth(self, client):
        response = await client.get("/api/v1/exam/questions")
        assert response.status_code in [401, 403]


class TestAttendanceAPI:
    """考勤API测试"""

    @pytest.mark.asyncio
    async def test_get_rules_missing_auth(self, client):
        response = await client.get("/api/v1/attendance/rules")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_check_in_missing_auth(self, client):
        response = await client.post("/api/v1/attendance/check-in", json={})
        assert response.status_code in [401, 403]


class TestNoticeAPI:
    """通知API测试"""

    @pytest.mark.asyncio
    async def test_get_notices_missing_auth(self, client):
        response = await client.get("/api/v1/notice/notices")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_create_notice_missing_auth(self, client):
        response = await client.post("/api/v1/notice/notices", json={"title": "测试"})
        assert response.status_code in [401, 403]


class TestAPIResponseFormat:
    """API响应格式测试"""

    @pytest.mark.asyncio
    async def test_root_response_format(self, client):
        response = await client.get("/")
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_health_check_response(self, client):
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
