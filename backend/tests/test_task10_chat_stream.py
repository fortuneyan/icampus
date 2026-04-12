# -*- coding: utf-8 -*-
"""
T10 测试脚本：AI 对话流式 SSE 功能

测试目标：验证 chat_stream 端点能正确返回 SSE 流式响应

运行方式：
    cd smart-campus/backend
    python -m pytest tests/test_task10_chat_stream.py -v

通过条件：所有测试用例通过后方可将 T10 标记为完成
"""

import pytest
import sys
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# =====================================================================
# 静态代码检查：确认流式相关代码已实现
# =====================================================================

class TestChatStreamStaticCheck:
    """验证流式 SSE 代码已添加到 chat.py"""

    def _get_chat_source(self):
        path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1', 'ai', 'chat.py'
        )
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _get_service_source(self):
        path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'services', 'ai_service.py'
        )
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_chat_py_has_stream_endpoint(self):
        """chat.py 应包含 /chat/stream 端点"""
        source = self._get_chat_source()
        assert '/chat/stream' in source or 'chat/stream' in source, (
            "FAIL: chat.py 缺少 /chat/stream 端点"
        )

    def test_chat_py_imports_stream_response(self):
        """chat.py 应导入 StreamingResponse"""
        source = self._get_chat_source()
        assert 'StreamingResponse' in source, (
            "FAIL: chat.py 未导入 StreamingResponse from fastapi.responses"
        )

    def test_service_has_stream_method(self):
        """ai_service.py 应包含流式方法"""
        source = self._get_service_source()
        has_stream = (
            'chat_stream' in source or
            'stream_chat' in source or
            'async_generator' in source or
            'yield' in source
        )
        assert has_stream, (
            "FAIL: ai_service.py 缺少流式方法（chat_stream / async_generator / yield）"
        )

    def test_no_simulated_response_in_stream_method(self):
        """ai_service.py 中的流式方法不应包含模拟响应字符串"""
        source = self._get_service_source()

        # 提取所有包含 yield 或 chat_stream 的函数
        lines = source.split('\n')
        stream_methods = []
        for i, line in enumerate(lines):
            if 'yield' in line or 'chat_stream' in line or 'stream_chat' in line:
                # 取上下文 5 行
                start = max(0, i - 2)
                end = min(len(lines), i + 20)
                stream_methods.append('\n'.join(lines[start:end]))

        for method_code in stream_methods:
            if 'def ' in method_code or 'async def' in method_code:
                assert '模拟响应' not in method_code, (
                    f"FAIL: 流式方法中仍包含 '模拟响应' 字符串"
                )
                assert 'AI回复:' not in method_code, (
                    f"FAIL: 流式方法中仍包含硬编码 'AI回复:' 前缀"
                )


# =====================================================================
# 路由端点存在性测试
# =====================================================================

class TestChatStreamEndpointExists:
    """测试流式端点已在路由中注册"""

    def test_chat_router_importable(self):
        """chat.py 可正常导入（无语法错误）"""
        try:
            from app.api.v1.ai import chat
            assert chat is not None
        except ImportError as e:
            pytest.fail(f"FAIL: chat.py 导入失败: {e}")

    def test_router_has_stream_function(self):
        """chat router 应包含 chat_stream 函数"""
        try:
            from app.api.v1.ai import chat
            assert hasattr(chat, 'chat_stream'), (
                "FAIL: chat router 缺少 chat_stream 函数"
            )
        except ImportError:
            pytest.skip("chat.py 未实现，跳过")


# =====================================================================
# 服务层流式方法测试（单元测试）
# =====================================================================

class TestAIServiceStream:
    """测试 ai_service.py 的流式方法"""

    @pytest.mark.asyncio
    async def test_service_has_chat_stream_method(self):
        """AIService 应具有流式方法"""
        try:
            from app.services.ai_service import AIService
            service = AIService(AsyncMock())
            has_stream = (
                hasattr(service, 'chat_stream') or
                hasattr(service, 'stream_chat') or
                hasattr(service, 'chat_with_stream')
            )
            assert has_stream, (
                "FAIL: AIService 缺少流式方法（chat_stream / stream_chat / chat_with_stream）"
            )
        except ImportError:
            pytest.skip("AIService 无法导入，跳过")

    @pytest.mark.asyncio
    async def test_stream_method_is_async_generator(self):
        """流式方法应为异步生成器（async def + yield）"""
        try:
            from app.services.ai_service import AIService
            import inspect
            service = AIService(AsyncMock())

            for method_name in ['chat_stream', 'stream_chat', 'chat_with_stream']:
                if hasattr(service, method_name):
                    method = getattr(service, method_name)
                    # 异步生成器：isasyncgenfunction 返回 True，iscoroutinefunction 返回 False
                    is_async_gen = (
                        inspect.isasyncgenfunction(method) or
                        inspect.iscoroutinefunction(method)
                    )
                    assert is_async_gen, (
                        f"FAIL: {method_name} 不是异步生成器 "
                        f"(iscoroutine={inspect.iscoroutinefunction(method)}, "
                        f"isasyncgen={inspect.isasyncgenfunction(method)})"
                    )
                    return
            pytest.skip("流式方法不存在，跳过")
        except ImportError:
            pytest.skip("AIService 无法导入，跳过")

    @pytest.mark.asyncio
    async def test_stream_method_yields_content(self):
        """流式方法应 yield 内容（非空）"""
        try:
            from app.services.ai_service import AIService

            mock_db = AsyncMock()
            mock_config = MagicMock()
            mock_config.api_key = None  # 未配置，快速返回

            service = AIService(mock_db)

            # 找到流式方法
            method_name = None
            for name in ['chat_stream', 'stream_chat', 'chat_with_stream']:
                if hasattr(service, name):
                    method_name = name
                    break

            if method_name is None:
                pytest.skip("流式方法不存在，跳过")

            with patch.object(service, 'get_config', return_value=mock_config), \
                 patch.object(service, 'create_session', return_value=MagicMock(id='test-session')), \
                 patch.object(service, 'add_message', return_value=MagicMock()):

                method = getattr(service, method_name)
                chunks = []
                async for chunk in method('user-id', '你好', None, 'deepseek'):
                    chunks.append(chunk)
                    break  # 至少有一个 chunk

            assert len(chunks) > 0, "FAIL: 流式方法未返回任何数据块"
            # 数据块应是字符串类型
            assert isinstance(chunks[0], str), (
                f"FAIL: 流式数据块应为 str，实际: {type(chunks[0])}"
            )
        except ImportError:
            pytest.skip("AIService 无法导入，跳过")

    @pytest.mark.asyncio
    async def test_stream_handles_unconfigured_api_key(self):
        """未配置 API Key 时流式方法应返回提示而非模拟响应"""
        try:
            from app.services.ai_service import AIService

            mock_db = AsyncMock()
            mock_config = MagicMock()
            mock_config.api_key = None

            service = AIService(mock_db)

            method_name = None
            for name in ['chat_stream', 'stream_chat', 'chat_with_stream']:
                if hasattr(service, name):
                    method_name = name
                    break

            if method_name is None:
                pytest.skip("流式方法不存在，跳过")

            with patch.object(service, 'get_config', return_value=mock_config), \
                 patch.object(service, 'create_session', return_value=MagicMock(id='test-session')), \
                 patch.object(service, 'add_message', return_value=MagicMock()):

                method = getattr(service, method_name)
                chunks = []
                full_text = ''
                async for chunk in method('user-id', '你好', None, 'deepseek'):
                    chunks.append(chunk)
                    full_text += chunk

            # 不应包含"模拟响应"
            assert '模拟响应' not in full_text, (
                f"FAIL: 未配置 API Key 时返回了模拟响应: {full_text}"
            )
        except ImportError:
            pytest.skip("AIService 无法导入，跳过")


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
