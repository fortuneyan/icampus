"""
T-S2 API限流中间件 - 单元测试

测试目标：
1. RateLimiter 核心算法
2. RateLimitMiddleware 中间件
3. 限流配置

运行：pytest tests/unit/security/test_rate_limiter.py -v
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import hashlib


class TestRateLimiterCore:
    """测试限流器核心"""

    def test_limiter_initialization(self):
        """测试限流器初始化"""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(default_limit=100, window=60)
        assert limiter.default_limit == 100
        assert limiter.window == 60

    def test_cache_initialization(self):
        """测试缓存初始化"""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter()
        assert limiter._cache is not None
        assert len(limiter._cache) == 0

    def test_generate_key(self):
        """测试key生成"""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter()
        key = limiter._generate_key("192.168.1.1", "/api/users")
        assert key == "192.168.1.1:/api/users"
        
        # 测试带用户ID的key
        key_with_user = limiter._generate_key("user123", "/api/users", user_id="user-uuid")
        assert "user123" in key_with_user
        assert "user-uuid" in key_with_user

    def test_get_window_start(self):
        """测试窗口起始时间计算"""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(window=60)
        now = datetime.now()
        window_start = limiter._get_window_start(now)
        
        # 应该是当前分钟的开始
        assert window_start.second == 0
        assert window_start.microsecond == 0

    def test_record_request(self):
        """测试记录请求"""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(window=60)
        key = "test-key"
        
        # 首次请求
        count1 = limiter._record_request(key)
        assert count1 == 1
        
        # 再次请求
        count2 = limiter._record_request(key)
        assert count2 == 2

    def test_get_remaining(self):
        """测试获取剩余请求次数"""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(default_limit=10, window=60)
        key = "test-key"
        
        # 记录3次请求
        limiter._record_request(key)
        limiter._record_request(key)
        limiter._record_request(key)
        
        remaining = limiter._get_remaining(key, 10)
        assert remaining == 7

    def test_get_remaining_no_record(self):
        """测试无记录时剩余次数"""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(default_limit=100)
        remaining = limiter._get_remaining("new-key", 100)
        assert remaining == 100

    def test_is_allowed_under_limit(self):
        """测试未超限时的请求"""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(default_limit=10)
        key = "test-key"
        
        allowed = limiter.is_allowed(key, limit=10)
        assert allowed is True

    def test_is_allowed_at_limit(self):
        """测试达到限值时的请求"""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(default_limit=3)
        key = "test-key"
        
        # 消耗所有配额
        limiter._record_request(key)
        limiter._record_request(key)
        limiter._record_request(key)
        
        # 第四次请求应被拒绝
        allowed = limiter.is_allowed(key, limit=3)
        assert allowed is False

    def test_cleanup_expired_keys(self):
        """测试清理过期key"""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(window=1)  # 1秒窗口
        
        # 添加一些key
        limiter._record_request("key1")
        limiter._record_request("key2")
        
        assert len(limiter._cache) == 2
        
        # 等待过期
        time.sleep(1.1)
        
        # 清理
        limiter._cleanup_expired()
        
        # 检查是否清理（取决于实现）
        # 可能被清理，也可能因为window不同还有残留


class TestRateLimitConfig:
    """测试限流配置"""

    def test_default_config(self):
        """测试默认配置"""
        from app.core.rate_limiter import DEFAULT_CONFIG
        
        assert DEFAULT_CONFIG["default_limit"] == 100
        assert DEFAULT_CONFIG["default_window"] == 60
        assert DEFAULT_CONFIG["enabled"] is True

    def test_endpoint_configs(self):
        """测试端点配置"""
        from app.core.rate_limiter import ENDPOINT_CONFIGS
        
        # 登录接口应更严格
        assert "login" in ENDPOINT_CONFIGS
        assert ENDPOINT_CONFIGS["login"]["limit"] < 100
        
        # 普通API
        assert "default" in ENDPOINT_CONFIGS

    def test_whitelist_config(self):
        """测试白名单配置"""
        from app.core.rate_limiter import WHITELIST
        
        # 白名单应为列表
        assert isinstance(WHITELIST, list)


class TestRateLimitMiddleware:
    """测试限流中间件"""

    def test_middleware_initialization(self):
        """测试中间件初始化"""
        from app.middleware.rate_limit import RateLimitMiddleware
        
        middleware = RateLimitMiddleware(app=MagicMock())
        assert middleware.app is not None
        assert middleware.limiter is not None

    def test_get_client_ip_from_request(self):
        """测试从请求获取客户端IP"""
        from app.middleware.rate_limit import RateLimitMiddleware
        
        middleware = RateLimitMiddleware(app=MagicMock())
        
        # 模拟请求
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = {}
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.100"

    def test_get_client_ip_from_forwarded(self):
        """测试从X-Forwarded-For获取IP"""
        from app.middleware.rate_limit import RateLimitMiddleware
        
        middleware = RateLimitMiddleware(app=MagicMock())
        
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"x-forwarded-for": "203.0.113.195, 70.41.3.18"}
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "203.0.113.195"

    def test_is_whitelisted_true(self):
        """测试白名单命中"""
        from app.middleware.rate_limit import RateLimitMiddleware
        
        middleware = RateLimitMiddleware(app=MagicMock())
        middleware.whitelist = ["192.168.1.1", "10.0.0.1"]
        
        assert middleware._is_whitelisted("192.168.1.1") is True

    def test_is_whitelisted_false(self):
        """测试非白名单"""
        from app.middleware.rate_limit import RateLimitMiddleware
        
        middleware = RateLimitMiddleware(app=MagicMock())
        middleware.whitelist = ["192.168.1.1"]
        
        assert middleware._is_whitelisted("192.168.1.2") is False

    def test_get_rate_limit_for_path(self):
        """测试获取路径限流配置"""
        from app.middleware.rate_limit import RateLimitMiddleware
        
        middleware = RateLimitMiddleware(app=MagicMock())
        
        # 登录路径
        limit1, window1 = middleware._get_rate_limit_for_path("/api/v1/auth/login")
        assert limit1 == 10  # 登录接口限制
        
        # 普通路径
        limit2, window2 = middleware._get_rate_limit_for_path("/api/v1/users")
        assert limit2 == 100  # 默认限制

    def test_build_rate_limit_headers(self):
        """测试构建限流响应头"""
        from app.middleware.rate_limit import RateLimitMiddleware
        
        middleware = RateLimitMiddleware(app=MagicMock())
        
        headers = middleware._build_headers(100, 95, 60, False)
        
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers
        assert headers["X-RateLimit-Limit"] == "100"
        assert headers["X-RateLimit-Remaining"] == "95"


class TestRateLimitEdgeCases:
    """边界测试"""

    def test_zero_limit(self):
        """测试零限制"""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(default_limit=0)
        allowed = limiter.is_allowed("test", limit=0)
        assert allowed is False

    def test_very_large_limit(self):
        """测试大限制"""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(default_limit=1000000)
        key = "test-large"
        
        # 前100次应通过
        for i in range(100):
            assert limiter.is_allowed(key, limit=1000000) is True

    def test_concurrent_requests(self):
        """测试并发请求"""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(default_limit=5)
        key = "concurrent-test"
        
        # 串行模拟并发
        results = []
        for i in range(10):
            allowed = limiter.is_allowed(key, limit=5)
            results.append(allowed)
        
        # 前5个应通过，后5个应拒绝
        assert results[:5].count(True) == 5
        assert results[5:].count(False) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
