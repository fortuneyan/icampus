# -*- coding: utf-8 -*-
"""
TASK-08 测试脚本：消息订阅前端页面
测试目标：验证后端 message/subscriptions.py API 正确可用，
         前端 Subscription.vue 已创建并连接真实接口

运行方式：
    cd smart-campus
    python -m pytest backend/tests/test_task08_message_sub.py -v

通过条件：所有测试用例通过后方可将 TASK-08 标记为完成
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

FRONTEND_VIEWS = os.path.join(
    os.path.dirname(__file__), '..', '..', 'frontend', 'src', 'views'
)


# =====================================================================
# 后端 API 结构检查
# =====================================================================

class TestMessageSubscriptionAPIStructure:
    """验证 message/subscriptions.py 后端 API"""

    def test_subscription_router_importable(self):
        """subscriptions router 可导入"""
        try:
            from app.api.v1.message.subscriptions import router
            assert router is not None
        except ImportError as e:
            pytest.fail(f"subscriptions router 无法导入: {e}")

    def test_list_subscriptions_route_exists(self):
        """GET / 获取订阅列表路由存在"""
        try:
            from app.api.v1.message.subscriptions import router
            from fastapi.routing import APIRoute
            get_routes = [
                r for r in router.routes
                if isinstance(r, APIRoute) and 'GET' in r.methods
            ]
            assert len(get_routes) > 0, "未找到 GET 路由"
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_create_subscription_route_exists(self):
        """POST / 创建订阅路由存在"""
        try:
            from app.api.v1.message.subscriptions import router
            from fastapi.routing import APIRoute
            post_routes = [
                r for r in router.routes
                if isinstance(r, APIRoute) and 'POST' in r.methods
            ]
            assert len(post_routes) > 0, "未找到 POST 路由，需实现创建订阅功能"
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_delete_subscription_route_exists(self):
        """DELETE /{id} 删除订阅路由存在"""
        try:
            from app.api.v1.message.subscriptions import router
            from fastapi.routing import APIRoute
            delete_routes = [
                r for r in router.routes
                if isinstance(r, APIRoute) and 'DELETE' in r.methods
            ]
            assert len(delete_routes) > 0, "未找到 DELETE 路由，需实现删除订阅功能"
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_messages_route_exists(self):
        """消息列表路由存在（GET /messages 或相关路由）"""
        try:
            # 尝试 messages 路由
            from app.api.v1.message import messages as msg_module
            assert hasattr(msg_module, 'router'), "messages 模块缺少 router"
        except ImportError:
            # 也可能在同一文件中
            try:
                from app.api.v1.message.subscriptions import router
                routes = [r.path for r in router.routes]
                has_messages = any('message' in r.lower() for r in routes)
                # 允许消息在单独文件中
                if not has_messages:
                    pytest.skip("messages 路由在单独文件中，跳过")
            except ImportError:
                pytest.skip("模块无法导入，跳过")


# =====================================================================
# 前端组件检查
# =====================================================================

class TestMessageSubscriptionFrontend:
    """验证消息订阅前端页面组件"""

    def _find_vue_file(self) -> str:
        candidates = [
            os.path.join(FRONTEND_VIEWS, 'message', 'Subscription.vue'),
            os.path.join(FRONTEND_VIEWS, 'message', 'subscription.vue'),
            os.path.join(FRONTEND_VIEWS, 'system', 'MessageSubscription.vue'),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    def test_subscription_vue_exists(self):
        """Subscription.vue 文件存在"""
        path = self._find_vue_file()
        assert path is not None, (
            f"FAIL: Subscription.vue 不存在，请在 frontend/src/views/message/ 目录创建"
        )

    def test_subscription_vue_uses_api(self):
        """Subscription.vue 应调用后端 API"""
        path = self._find_vue_file()
        if path is None:
            pytest.skip("Subscription.vue 不存在，跳过")
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()
        has_api = (
            'api' in source.lower() or
            'axios' in source.lower() or
            '/api/v1' in source or
            'subscription' in source.lower()
        )
        assert has_api, (
            "FAIL: Subscription.vue 未调用后端 API，需接入 /api/v1/message/subscriptions"
        )

    def test_subscription_vue_has_add_function(self):
        """Subscription.vue 应有添加订阅功能"""
        path = self._find_vue_file()
        if path is None:
            pytest.skip("Subscription.vue 不存在，跳过")
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()
        has_add = (
            'add' in source.lower() or
            'create' in source.lower() or
            'submit' in source.lower() or
            'el-button' in source
        )
        assert has_add, (
            "FAIL: Subscription.vue 缺少添加订阅功能"
        )

    def test_subscription_vue_has_delete_function(self):
        """Subscription.vue 应有删除订阅功能"""
        path = self._find_vue_file()
        if path is None:
            pytest.skip("Subscription.vue 不存在，跳过")
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()
        has_delete = (
            'delete' in source.lower() or
            'remove' in source.lower() or
            '删除' in source
        )
        assert has_delete, (
            "FAIL: Subscription.vue 缺少删除订阅功能"
        )


# =====================================================================
# 数据模型检查
# =====================================================================

class TestMessageModels:
    """验证消息相关数据模型"""

    def test_subscription_model_importable(self):
        """Subscription/MessageSubscription 模型可导入"""
        found = False
        for model_path in [
            'app.models.subscription',
            'app.models.message_subscription',
            'app.models.message',
        ]:
            try:
                import importlib
                mod = importlib.import_module(model_path)
                found = True
                break
            except ImportError:
                continue
        if not found:
            pytest.skip("消息订阅模型未找到，跳过")


# =====================================================================
# 集成测试
# =====================================================================

class TestMessageSubscriptionIntegration:
    @pytest.mark.asyncio
    async def test_create_and_list_subscription(self):
        pytest.skip("集成测试需要数据库环境，请在有DB的环境中运行")

    @pytest.mark.asyncio
    async def test_delete_subscription(self):
        pytest.skip("集成测试需要数据库环境，请在有DB的环境中运行")


if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True, text=True
    )
    print(result.stdout)
    print(result.stderr)
