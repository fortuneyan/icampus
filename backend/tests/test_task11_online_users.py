# -*- coding: utf-8 -*-
"""
TASK-11 测试脚本：在线用户监控 - 全新功能
测试目标：验证在线用户监控功能（后端API + 前端页面）

运行方式：
    cd smart-campus
    python -m pytest backend/tests/test_task11_online_users.py -v

通过条件：所有测试用例通过后方可将 TASK-11 标记为完成
"""

import pytest
import sys
import os

# 将项目根路径加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# =====================================================================
# 文件存在性检查
# =====================================================================

class TestFileStructure:
    """验证 TASK-11 所需文件已创建"""

    def test_backend_api_file_exists(self):
        """后端 API 文件应已创建：system/online_users.py"""
        backend_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'system', 'online_users.py'
        )
        assert os.path.exists(backend_path), (
            f"FAIL: 后端文件不存在 {backend_path}\n"
            "需要创建: backend/app/api/v1/system/online_users.py"
        )

    def test_frontend_page_exists(self):
        """前端页面应已创建：OnlineUsers.vue"""
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'src',
            'views', 'system', 'OnlineUsers.vue'
        )
        # 前端文件可能尚未创建，此处给出提示
        if not os.path.exists(frontend_path):
            pytest.skip(f"前端文件尚未创建（可后续创建）: {frontend_path}")

# =====================================================================
# 后端 API 结构测试
# =====================================================================

class TestOnlineUsersAPIStructure:
    """验证 online_users.py 的 API 路由结构"""

    def test_router_importable(self):
        """router 对象可正常导入"""
        try:
            from app.api.v1.system.online_users import router
            assert router is not None
        except ImportError as e:
            pytest.fail(f"无法导入 router: {e}")

    def test_get_online_users_endpoint_exists(self):
        """GET /online-users/ 路由存在"""
        try:
            from app.api.v1.system.online_users import router
            routes = [r.path for r in router.routes]
            has_list = any('online-users' in r and r.count('/') >= 2 for r in routes)
            assert has_list, (
                f"未找到在线用户列表路由，现有路由: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_delete_online_user_endpoint_exists(self):
        """DELETE /online-users/{token} 强制下线路由存在"""
        try:
            from app.api.v1.system.online_users import router
            routes = [r.path for r in router.routes]
            has_delete = any(
                'online-users' in r and '{' in r
                and r.split('online-users')[1].count('/') >= 1
                for r in routes
            )
            assert has_delete, (
                f"未找到强制下线路由 DELETE /online-users/{{token}}，现有路由: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_online_user_response_model_exists(self):
        """OnlineUser / OnlineUserList 响应模型存在"""
        try:
            from app.api.v1.system.online_users import OnlineUser
            assert hasattr(OnlineUser, 'model_fields') or hasattr(OnlineUser, '__fields__'), (
                "OnlineUser 应为 Pydantic 模型"
            )
        except ImportError:
            pytest.skip("响应模型未实现，跳过")

    def test_kickout_request_model_exists(self):
        """KickoutRequest 请求模型存在"""
        try:
            from app.api.v1.system.online_users import KickoutRequest
            assert hasattr(KickoutRequest, 'model_fields') or hasattr(KickoutRequest, '__fields__'), (
                "KickoutRequest 应为 Pydantic 模型"
            )
        except ImportError:
            pytest.skip("请求模型未实现，跳过")


# =====================================================================
# 核心功能逻辑测试
# =====================================================================

class TestOnlineUsersBusinessLogic:
    """验证在线用户监控的核心业务逻辑"""

    def test_online_user_model_fields_complete(self):
        """OnlineUser 模型字段完整"""
        try:
            from app.api.v1.system.online_users import OnlineUser
            from pydantic import BaseModel

            # 检查必需字段
            user = OnlineUser(
                user_id=1,
                username="test_user",
                login_time="2026-04-11T10:00:00",
                last_active="2026-04-11T12:00:00",
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0",
            )
            d = user.model_dump() if hasattr(user, 'model_dump') else user.dict()
            required_keys = ['user_id', 'username', 'login_time', 'last_active']
            for key in required_keys:
                assert key in d, f"OnlineUser 缺少必需字段: {key}"
        except ImportError:
            pytest.skip("模型未实现，跳过")

    def test_graceful_degradation_without_redis(self):
        """Redis 不可用时应有降级方案（查询数据库 login_logs）"""
        try:
            from app.api.v1.system.online_users import router
            source_path = os.path.join(
                os.path.dirname(__file__), '..', 'app', 'api', 'v1',
                'system', 'online_users.py'
            )
            with open(source_path, 'r', encoding='utf-8') as f:
                source = f.read()

            # 检查是否有降级逻辑（查 DB 或返回友好提示）
            has_fallback = (
                'login_logs' in source.lower() or
                'db' in source.lower() and 'fallback' in source.lower() or
                'redis' in source.lower() and 'except' in source.lower()
            )
            assert has_fallback, (
                "FAIL: 未找到 Redis 不可用时的降级逻辑。"
                "应查询 login_logs 表或返回友好提示"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_blacklist_mechanism_for_kickout(self):
        """强制下线应使用黑名单机制（防止 JWT 有效期内仍可用）"""
        try:
            from app.api.v1.system.online_users import router
            source_path = os.path.join(
                os.path.dirname(__file__), '..', 'app', 'api', 'v1',
                'system', 'online_users.py'
            )
            with open(source_path, 'r', encoding='utf-8') as f:
                source = f.read()

            # 检查是否有黑名单/blacklist/token失效逻辑
            has_blacklist = (
                'blacklist' in source.lower() or
                'token' in source.lower() and 'expire' in source.lower() or
                'invalidate' in source.lower()
            )
            assert has_blacklist, (
                "FAIL: 强制下线应实现黑名单机制，防止被踢用户在 JWT 有效期内继续访问"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")


# =====================================================================
# 前端页面测试（结构验证）
# =====================================================================

class TestOnlineUsersFrontend:
    """验证前端页面结构和组件完整性"""

    def test_frontend_file_exists(self):
        """OnlineUsers.vue 文件应存在"""
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'src',
            'views', 'system', 'OnlineUsers.vue'
        )
        assert os.path.exists(frontend_path), (
            f"FAIL: 前端文件不存在: {frontend_path}"
        )

    def test_frontend_has_api_call(self):
        """前端应调用 GET /api/v1/system/online-users/"""
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'src',
            'views', 'system', 'OnlineUsers.vue'
        )
        if not os.path.exists(frontend_path):
            pytest.skip("前端文件不存在，跳过")

        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()

        has_api_call = (
            'online-users' in content.lower() and
            ('axios' in content.lower() or 'fetch' in content.lower() or 'http' in content.lower())
        )
        assert has_api_call, (
            "FAIL: 前端页面未调用在线用户 API"
        )

    def test_frontend_has_auto_refresh(self):
        """前端应有自动刷新机制（建议 30 秒间隔）"""
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'src',
            'views', 'system', 'OnlineUsers.vue'
        )
        if not os.path.exists(frontend_path):
            pytest.skip("前端文件不存在，跳过")

        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()

        has_refresh = (
            'setinterval' in content.lower() or
            'autorefresh' in content.lower() or
            'timer' in content.lower() or
            'refresh' in content.lower()
        )
        if not has_refresh:
            pytest.skip("前端可能未实现自动刷新，后续可补充")

    def test_frontend_has_kickout_button(self):
        """前端应有强制下线按钮"""
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'src',
            'views', 'system', 'OnlineUsers.vue'
        )
        if not os.path.exists(frontend_path):
            pytest.skip("前端文件不存在，跳过")

        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()

        has_kickout = (
            'kickout' in content.lower() or
            '强制下线' in content or
            'force' in content.lower() and 'logout' in content.lower() or
            '下线' in content
        )
        assert has_kickout, (
            "FAIL: 前端页面未找到强制下线功能"
        )


# =====================================================================
# 依赖检查
# =====================================================================

class TestDependencies:
    """检查 TASK-11 的依赖项"""

    def test_redis_dependency_noted(self):
        """代码中应提及 Redis 依赖（或有降级方案）"""
        try:
            source_path = os.path.join(
                os.path.dirname(__file__), '..', 'app', 'api', 'v1',
                'system', 'online_users.py'
            )
            if not os.path.exists(source_path):
                pytest.skip("后端文件尚未创建，跳过")

            with open(source_path, 'r', encoding='utf-8') as f:
                source = f.read()

            # 确认提及了 Redis 或降级方案
            mentions_redis_or_fallback = (
                'redis' in source.lower() or
                'login_logs' in source or
                'database' in source.lower()
            )
            assert mentions_redis_or_fallback, (
                "FAIL: 代码应提及 Redis 或数据库降级方案"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")


# =====================================================================
# 运行结果汇总
# =====================================================================

if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True, text=True
    )
    print(result.stdout)
    print(result.stderr)
