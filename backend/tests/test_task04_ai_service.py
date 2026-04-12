# -*- coding: utf-8 -*-
"""
TASK-04 测试脚本：AI 对话服务 — 接入真实 LLM API
测试目标：验证 ai_service.py chat() 方法不再返回"模拟响应"字符串，
         能正确处理配置/未配置/错误等场景

运行方式：
    cd smart-campus
    python -m pytest backend/tests/test_task04_ai_service.py -v

通过条件：所有测试用例通过后方可将 TASK-04 标记为完成
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# =====================================================================
# 静态代码检查：确认模拟响应字符串已移除
# =====================================================================

class TestNoMockResponse:
    """验证 ai_service.py 中模拟响应已被移除"""

    def _get_source(self):
        path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'services', 'ai_service.py'
        )
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_no_simulated_response_string(self):
        """'模拟响应' 字符串应已移除"""
        source = self._get_source()
        assert '模拟响应' not in source, (
            "FAIL: 代码中仍包含 '模拟响应' 字符串，需替换为真实 LLM API 调用"
        )

    def test_no_hardcoded_ai_prefix(self):
        """'AI回复:' 硬编码前缀应已移除"""
        source = self._get_source()
        assert '"AI回复:' not in source and "'AI回复:" not in source, (
            "FAIL: 代码中仍包含硬编码 'AI回复:' 前缀，需移除"
        )

    def test_has_llm_call_implementation(self):
        """代码应包含 LLM API 调用逻辑（_call_llm 或 httpx 调用）"""
        source = self._get_source()
        has_llm = (
            '_call_llm' in source or
            'httpx' in source or
            'openai' in source.lower() or
            'chat/completions' in source
        )
        assert has_llm, (
            "FAIL: 未发现 LLM API 调用代码（_call_llm/httpx/chat/completions），请实现真实接口调用"
        )

    def test_handles_no_api_key(self):
        """代码应处理未配置 API Key 的情况"""
        source = self._get_source()
        has_unconfig_handling = (
            '[未配置]' in source or
            'not config' in source.lower() or
            'api_key is None' in source or
            'not api_key' in source or
            'api_key not' in source
        )
        assert has_unconfig_handling, (
            "FAIL: 未发现 API Key 未配置时的处理逻辑，需添加相应判断"
        )

    def test_has_error_handling(self):
        """代码应有错误处理（try/except）"""
        source = self._get_source()
        assert 'except' in source, (
            "FAIL: 未发现异常处理逻辑，LLM 调用需要完善的 try/except"
        )


# =====================================================================
# 未配置场景测试（无需真实 API）
# =====================================================================

class TestAIServiceNoConfig:
    """测试未配置 API Key 时的行为"""

    @pytest.mark.asyncio
    async def test_chat_returns_unconfigured_message_when_no_api_key(self):
        """
        未配置 API Key 时，返回 [未配置] 开头的提示，而非模拟响应字符串
        """
        try:
            from app.services.ai_service import AIService

            # Mock DB session：get_config 返回无 API Key 的配置
            mock_db = AsyncMock()
            mock_config = MagicMock()
            mock_config.api_key = None
            mock_config.is_active = True

            service = AIService(mock_db)

            with patch.object(service, 'get_config', return_value=mock_config), \
                 patch.object(service, 'create_session', return_value=MagicMock(id='test-session-id')), \
                 patch.object(service, 'add_message', return_value=None), \
                 patch.object(service, 'get_session_messages', return_value=[]):

                result = await service.chat(
                    user_id='test-user-id',
                    message='你好',
                    model_type='deepseek'
                )

            # 验证：不应包含"模拟响应"
            message = result.get('message', '') if isinstance(result, dict) else str(result)
            assert '模拟响应' not in message, (
                f"FAIL: 未配置 API Key 时返回了模拟响应字符串: {message}"
            )
            # 验证：应包含未配置提示
            assert '[未配置]' in message or '未配置' in message or '[错误]' in message, (
                f"FAIL: 未配置 API Key 时应返回明确的未配置提示，实际返回: {message}"
            )
        except ImportError:
            pytest.skip("AIService 无法导入，跳过")

    @pytest.mark.asyncio
    async def test_chat_returns_unconfigured_when_config_is_none(self):
        """
        数据库中无该 model_type 的配置记录时，返回未配置提示
        """
        try:
            from app.services.ai_service import AIService

            mock_db = AsyncMock()
            service = AIService(mock_db)

            with patch.object(service, 'get_config', return_value=None), \
                 patch.object(service, 'create_session', return_value=MagicMock(id='test-session-id')), \
                 patch.object(service, 'add_message', return_value=None), \
                 patch.object(service, 'get_session_messages', return_value=[]):

                result = await service.chat(
                    user_id='test-user-id',
                    message='你好',
                    model_type='unknown_model'
                )

            message = result.get('message', '') if isinstance(result, dict) else str(result)
            assert '模拟响应' not in message, (
                f"FAIL: 无配置时返回了模拟响应字符串: {message}"
            )
        except ImportError:
            pytest.skip("AIService 无法导入，跳过")


# =====================================================================
# 错误处理测试（Mock HTTP 客户端）
# =====================================================================

class TestAIServiceErrorHandling:
    """测试各种 API 调用失败场景"""

    @pytest.mark.asyncio
    async def test_api_timeout_returns_error_message(self):
        """API 超时时返回 [错误] 提示，HTTP 状态仍为 200"""
        try:
            import httpx
            from app.services.ai_service import AIService

            mock_db = AsyncMock()
            mock_config = MagicMock()
            mock_config.api_key = "test-key"
            mock_config.base_url = "https://api.deepseek.com"
            mock_config.model_name = "deepseek-chat"
            mock_config.max_tokens = 2048
            mock_config.temperature = 0.7

            service = AIService(mock_db)

            async def mock_http_post(*args, **kwargs):
                raise httpx.TimeoutException("超时")

            with patch.object(service, 'get_config', return_value=mock_config), \
                 patch.object(service, 'create_session', return_value=MagicMock(id='test-session-id')), \
                 patch.object(service, 'add_message', return_value=None), \
                 patch.object(service, 'get_session_messages', return_value=[]), \
                 patch('httpx.AsyncClient') as mock_client:

                mock_client.return_value.__aenter__ = AsyncMock(
                    return_value=MagicMock(
                        post=AsyncMock(side_effect=httpx.TimeoutException("超时"))
                    )
                )
                mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

                result = await service.chat(
                    user_id='test-user-id',
                    message='你好',
                    model_type='deepseek'
                )

            message = result.get('message', '') if isinstance(result, dict) else str(result)
            assert '模拟响应' not in message
            assert '[错误]' in message or '超时' in message or 'timeout' in message.lower(), (
                f"FAIL: 超时时应返回错误提示，实际返回: {message}"
            )
        except ImportError:
            pytest.skip("依赖未安装，跳过")

    @pytest.mark.asyncio
    async def test_api_401_returns_invalid_key_message(self):
        """API 返回 401 时，提示 API Key 无效"""
        try:
            import httpx
            from app.services.ai_service import AIService

            mock_db = AsyncMock()
            mock_config = MagicMock()
            mock_config.api_key = "invalid-key"
            mock_config.base_url = "https://api.deepseek.com"
            mock_config.model_name = "deepseek-chat"
            mock_config.max_tokens = 2048
            mock_config.temperature = 0.7

            service = AIService(mock_db)

            # Mock 401 响应
            mock_response = MagicMock()
            mock_response.status_code = 401
            http_error = httpx.HTTPStatusError(
                "401 Unauthorized",
                request=MagicMock(),
                response=mock_response
            )

            with patch.object(service, 'get_config', return_value=mock_config), \
                 patch.object(service, 'create_session', return_value=MagicMock(id='test-session-id')), \
                 patch.object(service, 'add_message', return_value=None), \
                 patch.object(service, 'get_session_messages', return_value=[]), \
                 patch('httpx.AsyncClient') as mock_client:

                mock_post = AsyncMock()
                mock_post.raise_for_status = MagicMock(side_effect=http_error)
                mock_client.return_value.__aenter__ = AsyncMock(
                    return_value=MagicMock(post=AsyncMock(return_value=mock_post))
                )
                mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

                result = await service.chat(
                    user_id='test-user-id',
                    message='你好',
                    model_type='deepseek'
                )

            message = result.get('message', '') if isinstance(result, dict) else str(result)
            assert '模拟响应' not in message, (
                f"FAIL: 401 错误时仍返回模拟响应: {message}"
            )
        except ImportError:
            pytest.skip("依赖未安装，跳过")


# =====================================================================
# 成功调用测试（Mock LLM 返回成功响应）
# =====================================================================

class TestAIServiceSuccess:
    """测试 LLM API 调用成功场景"""

    @pytest.mark.asyncio
    async def test_successful_llm_call_returns_real_content(self):
        """
        LLM API 返回成功响应时，返回真实内容（非模拟响应）
        """
        try:
            import httpx
            from app.services.ai_service import AIService

            mock_db = AsyncMock()
            mock_config = MagicMock()
            mock_config.api_key = "test-valid-key"
            mock_config.base_url = "https://api.deepseek.com"
            mock_config.model_name = "deepseek-chat"
            mock_config.max_tokens = 2048
            mock_config.temperature = 0.7

            service = AIService(mock_db)

            # Mock 成功的 LLM 响应
            mock_llm_response = {
                "choices": [
                    {"message": {"content": "你好！我是 DeepSeek AI，有什么可以帮您的？"}}
                ]
            }

            # 使用 MagicMock 而非 AsyncMock：.json() 同步返回，匹配 _call_llm 的调用方式
            mock_response = MagicMock()
            mock_response.json.return_value = mock_llm_response
            mock_response.raise_for_status = MagicMock()
            mock_response.status_code = 200

            with patch.object(service, 'get_config', return_value=mock_config), \
                 patch.object(service, 'create_session', return_value=MagicMock(id='test-session-id')), \
                 patch.object(service, 'add_message', return_value=None), \
                 patch.object(service, 'get_session_messages', return_value=[]), \
                 patch('httpx.AsyncClient') as mock_client:

                mock_client.return_value.__aenter__ = AsyncMock(
                    return_value=MagicMock(post=MagicMock(return_value=mock_response))
                )
                mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

                result = await service.chat(
                    user_id='test-user-id',
                    message='你好',
                    model_type='deepseek'
                )

            message = result.get('message', '') if isinstance(result, dict) else str(result)
            assert '模拟响应' not in message, (
                f"FAIL: 成功响应时仍包含模拟响应字符串: {message}"
            )
            assert 'DeepSeek AI' in message or '你好' in message, (
                f"FAIL: 应返回 LLM 真实内容，实际返回: {message}"
            )
        except ImportError:
            pytest.skip("依赖未安装，跳过")

    @pytest.mark.asyncio
    async def test_chat_result_contains_session_id(self):
        """chat() 返回结果应包含 session_id 字段"""
        try:
            from app.services.ai_service import AIService

            mock_db = AsyncMock()
            mock_config = MagicMock()
            mock_config.api_key = None  # 未配置，快速返回

            service = AIService(mock_db)

            with patch.object(service, 'get_config', return_value=mock_config), \
                 patch.object(service, 'create_session', return_value=MagicMock(id='session-123')), \
                 patch.object(service, 'add_message', return_value=None), \
                 patch.object(service, 'get_session_messages', return_value=[]):

                result = await service.chat(
                    user_id='test-user-id',
                    message='你好',
                )

            if isinstance(result, dict):
                assert 'session_id' in result, (
                    f"FAIL: 返回结果缺少 session_id 字段，实际: {list(result.keys())}"
                )
        except ImportError:
            pytest.skip("AIService 无法导入，跳过")


# =====================================================================
# AIService 结构检查
# =====================================================================

class TestAIServiceStructure:
    """验证 AIService 的方法结构"""

    def test_ai_service_importable(self):
        """AIService 可正常导入"""
        try:
            from app.services.ai_service import AIService
            assert AIService is not None
        except ImportError as e:
            pytest.fail(f"AIService 无法导入: {e}")

    def test_ai_service_has_chat_method(self):
        """AIService 具有 chat 方法"""
        try:
            from app.services.ai_service import AIService
            assert hasattr(AIService, 'chat'), "AIService 缺少 chat 方法"
        except ImportError:
            pytest.skip("AIService 未实现，跳过")

    def test_ai_service_has_get_config_method(self):
        """AIService 具有 get_config 方法"""
        try:
            from app.services.ai_service import AIService
            assert hasattr(AIService, 'get_config'), "AIService 缺少 get_config 方法"
        except ImportError:
            pytest.skip("AIService 未实现，跳过")

    def test_httpx_in_requirements(self):
        """requirements.txt 应包含 httpx"""
        req_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'requirements.txt'
        )
        if not os.path.exists(req_path):
            pytest.skip("requirements.txt 不存在，跳过")
        with open(req_path, 'r') as f:
            content = f.read().lower()
        assert 'httpx' in content, (
            "FAIL: requirements.txt 未包含 httpx，需添加 httpx>=0.27.0"
        )


# =====================================================================
# 主函数
# =====================================================================

if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True, text=True
    )
    print(result.stdout)
    print(result.stderr)
