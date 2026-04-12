"""
T-S4 CSRF防护中间件 - 单元测试

测试目标：
1. CSRF Token生成和验证
2. CSRF中间件功能

Author: AI
Date: 2026-04-11
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


class TestCSRFToken:
    """测试CSRF Token"""

    def test_generate_token(self):
        """测试Token生成"""
        from app.core.csrf import CSRFToken
        
        token = CSRFToken.generate()
        assert token is not None
        assert len(token) == 64  # 32字节hex

    def test_generate_unique_tokens(self):
        """测试每次生成唯一Token"""
        from app.core.csrf import CSRFToken
        
        tokens = [CSRFToken.generate() for _ in range(10)]
        assert len(set(tokens)) == 10  # 全部唯一

    def test_verify_valid_token(self):
        """测试验证有效Token"""
        from app.core.csrf import CSRFToken
        
        token = CSRFToken.generate()
        stored = token  # 模拟存储
        
        result = CSRFToken.verify(token, stored)
        assert result is True

    def test_verify_invalid_token(self):
        """测试验证无效Token"""
        from app.core.csrf import CSRFToken
        
        token1 = CSRFToken.generate()
        token2 = CSRFToken.generate()
        
        result = CSRFToken.verify(token1, token2)
        assert result is False

    def test_generate_secret(self):
        """测试密钥生成"""
        from app.core.csrf import CSRFToken
        
        secret = CSRFToken.generate_secret()
        assert secret is not None
        assert len(secret) >= 32

    def test_token_with_secret(self):
        """测试带密钥的Token"""
        from app.core.csrf import CSRFToken
        
        secret = CSRFToken.generate_secret()
        token = CSRFToken.generate(secret)
        
        assert token is not None
        assert CSRFToken.verify(token, token, secret) is True


class TestCSRFConfig:
    """测试CSRF配置"""

    def test_default_config(self):
        """测试默认配置"""
        from app.core.csrf import CSRFConfig
        
        assert CSRFConfig.TOKEN_LENGTH == 32
        assert CSRFConfig.SECRET_LENGTH == 32
        assert CSRFConfig.TOKEN_NAME == "csrftoken"
        assert CSRFConfig.HEADER_NAME == "X-CSRF-Token"

    def test_cookie_config(self):
        """测试Cookie配置"""
        from app.core.csrf import CSRFConfig
        
        assert CSRFConfig.COOKIE_SECURE is not None
        assert CSRFConfig.COOKIE_HTTPONLY is False  # 前端需要读取
        assert CSRFConfig.COOKIE_SAMESITE in ["lax", "strict", "none"]


class TestCSRFUtils:
    """测试CSRF工具函数"""

    def test_mask_token(self):
        """测试Token遮蔽"""
        from app.core.csrf import CSRFUtils
        
        token = "abc123def456"
        masked = CSRFUtils.mask_token(token)
        assert masked != token
        assert len(masked) == len(token)

    def test_constant_time_compare(self):
        """测试常量时间比较"""
        from app.core.csrf import CSRFUtils
        
        # 相同
        assert CSRFUtils.constant_time_compare("test", "test") is True
        # 不同
        assert CSRFUtils.constant_time_compare("test", " Test") is False
        # 不同长度
        assert CSRFUtils.constant_time_compare("test", "testing") is False

    def test_generate_random_bytes(self):
        """测试随机字节生成"""
        from app.core.csrf import CSRFUtils
        
        bytes1 = CSRFUtils.generate_random_bytes(16)
        bytes2 = CSRFUtils.generate_random_bytes(16)
        
        assert len(bytes1) == 16
        assert bytes1 != bytes2  # 应该不同

    def test_hex_encode(self):
        """测试十六进制编码"""
        from app.core.csrf import CSRFUtils
        
        result = CSRFUtils.hex_encode(b"test")
        assert result == "74657374"  # "test"的hex


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
