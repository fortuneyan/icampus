import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_token,
)
from app.schemas.auth import LoginRequest


class TestSecurity:
    """安全模块测试"""

    def test_password_hash(self):
        """测试密码哈希"""
        password = "test123456"
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_password_verify_success(self):
        """测试密码验证成功"""
        password = "test123456"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_password_verify_fail(self):
        """测试密码验证失败"""
        password = "test123456"
        wrong_password = "wrong123456"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False

    def test_create_access_token(self):
        """测试创建访问令牌"""
        data = {"sub": "test-user-id", "username": "testuser"}
        token = create_access_token(data)
        assert token is not None
        assert len(token) > 0

    def test_decode_token(self):
        """测试解码令牌"""
        data = {"sub": "test-user-id", "username": "testuser"}
        token = create_access_token(data)
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "test-user-id"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"

    def test_decode_invalid_token(self):
        """测试解码无效令牌"""
        payload = decode_token("invalid-token")
        assert payload is None


class TestAuthSchemas:
    """认证 schemas 测试"""

    def test_login_request_valid(self):
        """测试登录请求验证"""
        request = LoginRequest(username="testuser", password="test123456")
        assert request.username == "testuser"
        assert request.password == "test123456"

    def test_login_request_username_min_length(self):
        """测试用户名最小长度验证"""
        with pytest.raises(Exception):
            LoginRequest(username="ab", password="test123456")

    def test_login_request_password_min_length(self):
        """测试密码最小长度验证"""
        with pytest.raises(Exception):
            LoginRequest(username="testuser", password="12345")


class TestResponseSchema:
    """响应 schemas 测试"""

    def test_success_response(self):
        """测试成功响应"""
        from app.schemas.response import success

        result = success({"user": "test"}, "登录成功")
        assert result["code"] == 200
        assert result["message"] == "登录成功"
        assert result["data"]["user"] == "test"

    def test_error_response(self):
        """测试错误响应"""
        from app.schemas.response import error

        result = error(401, "未授权")
        assert result["code"] == 401
        assert result["message"] == "未授权"

    def test_page_response(self):
        """测试分页响应"""
        from app.schemas.response import page_response

        items = [{"id": 1}, {"id": 2}]
        result = page_response(items, 2, 1, 10)
        assert result["code"] == 200
        assert result["data"]["items"] == items
        assert result["data"]["total"] == 2
        assert result["data"]["total_pages"] == 1


class TestConfig:
    """配置模块测试"""

    def test_settings_creation(self):
        """测试配置创建"""
        from app.core.config import settings

        assert settings.APP_NAME == "智慧校园管理平台"
        assert settings.DEBUG is True
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000

    def test_database_url_property(self):
        """测试数据库URL属性"""
        from app.core.config import Settings

        settings = Settings()
        expected = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        assert settings.DATABASE_URL == expected


class TestModels:
    """数据模型测试"""

    def test_user_model_creation(self):
        """测试用户模型存在"""
        from app.models.user import User

        assert User.__tablename__ == "users"
        assert hasattr(User, "username")
        assert hasattr(User, "email")
        assert hasattr(User, "department_id")
        assert hasattr(User, "position")

    def test_role_model_creation(self):
        """测试角色模型存在"""
        from app.models.role import Role

        assert Role.__tablename__ == "roles"
        assert hasattr(Role, "code")
        assert hasattr(Role, "name")
        assert hasattr(Role, "level")
        assert hasattr(Role, "data_scope")

    def test_permission_model_creation(self):
        """测试权限模型存在"""
        from app.models.role import Permission

        assert Permission.__tablename__ == "permissions"
        assert hasattr(Permission, "code")
        assert hasattr(Permission, "resource")
        assert hasattr(Permission, "action")


class TestExceptions:
    """异常模块测试"""

    def test_not_found_exception(self):
        """测试404异常"""
        from app.core.exceptions import NotFoundException

        exc = NotFoundException("用户不存在")
        assert exc.status_code == 404
        assert exc.detail == "用户不存在"

    def test_unauthorized_exception(self):
        """测试401异常"""
        from app.core.exceptions import UnauthorizedException

        exc = UnauthorizedException("请先登录")
        assert exc.status_code == 401
        assert exc.detail == "请先登录"

    def test_forbidden_exception(self):
        """测试403异常"""
        from app.core.exceptions import ForbiddenException

        exc = ForbiddenException("禁止访问")
        assert exc.status_code == 403
        assert exc.detail == "禁止访问"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
