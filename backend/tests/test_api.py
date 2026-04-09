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


class TestHealthEndpoints:
    """健康检查接口测试"""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """测试根路径"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """测试健康检查"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAuthAPI:
    """认证API测试 - 需要数据库"""

    @pytest.mark.asyncio
    async def test_login_missing_username(self, client):
        """测试缺少用户名"""
        response = await client.post(
            "/api/v1/auth/login", json={"password": "test123456"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_missing_password(self, client):
        """测试缺少密码"""
        response = await client.post(
            "/api/v1/auth/login", json={"username": "testuser"}
        )
        assert response.status_code == 422


class TestAuthMiddleware:
    """认证中间件测试 - 需要数据库"""

    @pytest.mark.asyncio
    async def test_get_me_without_token(self, client):
        """测试无token获取用户信息"""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_logout_without_token(self, client):
        """测试无token登出"""
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code in [401, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
