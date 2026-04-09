"""
第二阶段测试 - 系统管理模块
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.base_service import BaseService
from app.services.user_service import UserService
from app.services.dept_service import DepartmentService
from app.services.role_service import RoleService
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class TestBaseService:
    """BaseService 通用服务测试"""

    def test_service_creation(self):
        """测试服务创建"""

        class MockModel:
            pass

        assert BaseService(MockModel, None) is not None


class TestUserSchemas:
    """用户 Schemas 测试"""

    def test_user_create_valid(self):
        """测试用户创建验证"""
        user = UserCreate(
            username="testuser",
            password="password123",
            email="test@example.com",
            real_name="Test User",
        )
        assert user.username == "testuser"
        assert user.password == "password123"
        assert user.email == "test@example.com"

    def test_user_create_username_min_length(self):
        """测试用户名最小长度验证"""
        with pytest.raises(Exception):
            UserCreate(username="ab", password="password123")

    def test_user_create_password_min_length(self):
        """测试密码最小长度验证"""
        with pytest.raises(Exception):
            UserCreate(username="testuser", password="12345")

    def test_user_update_partial(self):
        """测试用户更新部分字段"""
        update = UserUpdate(real_name="New Name", email="new@example.com")
        assert update.real_name == "New Name"
        assert update.email == "new@example.com"


class TestSecurity:
    """安全模块扩展测试"""

    def test_password_hash_with_special_chars(self):
        """测试包含特殊字符的密码"""
        password = "P@ssw0rd!123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_password_hash_unicode(self):
        """测试包含中文的密码"""
        password = "密码123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True


class TestPaginationSchemas:
    """分页 Schemas 测试"""

    def test_page_params_default(self):
        """测试默认分页参数"""
        from app.schemas.pagination import PageParams

        params = PageParams()
        assert params.page == 1
        assert params.page_size == 20

    def test_page_params_custom(self):
        """测试自定义分页参数"""
        from app.schemas.pagination import PageParams

        params = PageParams(page=5, page_size=50)
        assert params.page == 5
        assert params.page_size == 50

    def test_page_params_validation(self):
        """测试分页参数验证"""
        from app.schemas.pagination import PageParams

        with pytest.raises(Exception):
            PageParams(page=0)
        with pytest.raises(Exception):
            PageParams(page_size=200)


class TestAPIEndpoints:
    """API接口结构测试"""

    def test_users_router_exists(self):
        """测试用户路由是否存在"""
        from app.api.v1.system.users import router

        assert router is not None
        assert len(router.routes) > 0

    def test_departments_router_exists(self):
        """测试部门路由是否存在"""
        from app.api.v1.system.departments import router

        assert router is not None

    def test_roles_router_exists(self):
        """测试角色路由是否存在"""
        from app.api.v1.system.roles import router

        assert router is not None


class TestServices:
    """服务层测试"""

    def test_user_service_can_be_instantiated(self):
        """测试用户服务可以实例化"""
        from unittest.mock import MagicMock

        mock_db = MagicMock()
        service = UserService(mock_db)
        assert service is not None

    def test_department_service_can_be_instantiated(self):
        """测试部门服务可以实例化"""
        from unittest.mock import MagicMock

        mock_db = MagicMock()
        service = DepartmentService(mock_db)
        assert service is not None

    def test_role_service_can_be_instantiated(self):
        """测试角色服务可以实例化"""
        from unittest.mock import MagicMock

        mock_db = MagicMock()
        service = RoleService(mock_db)
        assert service is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
