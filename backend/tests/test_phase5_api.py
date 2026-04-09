"""
第五阶段 API 测试 - 统计报表与系统设置
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


class TestDashboardAPI:
    """仪表盘API测试"""

    @pytest.mark.asyncio
    async def test_get_overview_missing_auth(self, client):
        response = await client.get("/api/v1/dashboard/overview")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_statistics_missing_auth(self, client):
        response = await client.get("/api/v1/dashboard/statistics")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_charts_missing_auth(self, client):
        response = await client.get("/api/v1/dashboard/charts")
        assert response.status_code in [401, 403]


class TestReportAPI:
    """报表API测试"""

    @pytest.mark.asyncio
    async def test_get_student_report_missing_auth(self, client):
        response = await client.get("/api/v1/report/student")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_score_report_missing_auth(self, client):
        response = await client.get("/api/v1/report/score")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_attendance_report_missing_auth(self, client):
        response = await client.get("/api/v1/report/attendance")
        assert response.status_code in [401, 403]


class TestSettingsAPI:
    """设置API测试"""

    @pytest.mark.asyncio
    async def test_get_config_missing_auth(self, client):
        response = await client.get("/api/v1/settings/config")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_system_info_missing_auth(self, client):
        response = await client.get("/api/v1/settings/system-info")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_logs_missing_auth(self, client):
        response = await client.get("/api/v1/settings/logs")
        assert response.status_code in [401, 403]


class TestMessageAPI:
    """消息API测试"""

    @pytest.mark.asyncio
    async def test_get_messages_missing_auth(self, client):
        response = await client.get("/api/v1/message/list")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_unread_count_missing_auth(self, client):
        response = await client.get("/api/v1/message/unread-count")
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
