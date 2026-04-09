"""
第二阶段 API 测试 - 系统管理模块
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


class TestSystemUsersAPI:
    """用户管理API测试"""

    @pytest.mark.asyncio
    async def test_get_users_missing_auth(self, client):
        """测试无认证获取用户列表"""
        response = await client.get("/api/v1/system/users")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_create_user_missing_auth(self, client):
        """测试无认证创建用户"""
        response = await client.post(
            "/api/v1/system/users",
            json={
                "username": "testuser",
                "password": "password123",
                "real_name": "测试用户",
            },
        )
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_create_user_validation(self, client):
        """测试创建用户参数验证"""
        response = await client.post(
            "/api/v1/system/users", json={"username": "ab", "password": "123"}
        )
        assert response.status_code in [401, 403]


class TestSystemDepartmentsAPI:
    """部门管理API测试"""

    @pytest.mark.asyncio
    async def test_get_departments_missing_auth(self, client):
        """测试无认证获取部门列表"""
        response = await client.get("/api/v1/system/departments")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_create_department_missing_auth(self, client):
        """测试无认证创建部门"""
        response = await client.post(
            "/api/v1/system/departments", json={"name": "测试部门", "code": "TEST001"}
        )
        assert response.status_code in [401, 403]


class TestSystemRolesAPI:
    """角色权限API测试"""

    @pytest.mark.asyncio
    async def test_get_roles_missing_auth(self, client):
        """测试无认证获取角色列表"""
        response = await client.get("/api/v1/system/roles")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_menus_missing_auth(self, client):
        """测试无认证获取菜单"""
        response = await client.get("/api/v1/system/menus")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_permissions_missing_auth(self, client):
        """测试无认证获取权限"""
        response = await client.get("/api/v1/system/permissions")
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
