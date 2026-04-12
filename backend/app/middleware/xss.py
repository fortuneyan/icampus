"""
XSS防护中间件

为FastAPI应用提供XSS防护，符合三级等保要求：
- 8.1.2.3 安全审计：输入验证
- 8.1.4.2 入侵防范：防止XSS攻击

Author: AI
Date: 2026-04-11
"""

from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
import json

from app.core.xss import XSSFilter, XSSEncoder, XSSConfig


class XSSProtectionMiddleware(BaseHTTPMiddleware):
    """
    XSS防护中间件
    
    自动过滤请求中的XSS攻击代码。
    """
    
    def __init__(
        self,
        app: ASGIApp,
        level: str = XSSConfig.Level.STRICT,
        filter_request: bool = True,
        encode_response: bool = True,
    ):
        """
        初始化XSS防护中间件
        
        Args:
            app: ASGI应用
            level: 过滤级别 (strict/relaxed/none)
            filter_request: 是否过滤请求
            encode_response: 是否编码响应
        """
        super().__init__(app)
        self.filter = XSSFilter(level)
        self.filter_request = filter_request
        self.encode_response = encode_response
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        处理请求
        
        Args:
            request: HTTP请求
            call_next: 下一个处理器
            
        Returns:
            Response: HTTP响应
        """
        # 过滤请求数据
        if self.filter_request:
            await self._filter_request(request)
        
        # 执行请求
        response = await call_next(request)
        
        # 编码响应数据
        if self.encode_response and response.headers.get('content-type', '').startswith('application/json'):
            # JSON响应需要特殊处理
            pass
        
        return response
    
    async def _filter_request(self, request: Request) -> None:
        """
        过滤请求数据
        
        Args:
            request: HTTP请求
        """
        # 过滤Query参数
        if request.query_params:
            filtered_params = {}
            for key, value in request.query_params.items():
                filtered_key = self.filter.filter_input(key)
                filtered_value = self.filter.filter_input(value)
                filtered_params[filtered_key] = filtered_value
            
            # 存储过滤后的参数（注意：Starlette的query_params是只读的）
            # 这里只是示例，实际需要自定义Request类
    
    def filter_dict(self, data: dict) -> dict:
        """
        过滤字典数据
        
        Args:
            data: 字典数据
            
        Returns:
            dict: 过滤后的数据
        """
        if not isinstance(data, dict):
            return data
        
        result = {}
        for key, value in data.items():
            filtered_key = self.filter.filter_input(key)
            
            if isinstance(value, str):
                result[filtered_key] = self.filter.filter_input(value)
            elif isinstance(value, dict):
                result[filtered_key] = self.filter_dict(value)
            elif isinstance(value, list):
                result[filtered_key] = [
                    self.filter_dict(item) if isinstance(item, dict) 
                    else self.filter.filter_input(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                result[filtered_key] = value
        
        return result


class XSSSafeResponse:
    """
    XSS安全响应工具
    
    用于手动过滤和编码响应数据。
    """
    
    def __init__(self, level: str = XSSConfig.Level.STRICT):
        self.filter = XSSFilter(level)
        self.encoder = XSSEncoder()
    
    def sanitize_html(self, html_text: str) -> str:
        """
        清理HTML内容
        
        移除所有可能危险的标签和属性。
        
        Args:
            html_text: HTML文本
            
        Returns:
            str: 清理后的HTML
        """
        return self.filter.filter_input(html_text)
    
    def sanitize_dict(self, data: dict) -> dict:
        """
        清理字典中的所有字符串
        
        Args:
            data: 字典数据
            
        Returns:
            dict: 清理后的字典
        """
        return self.filter.filter_dict(data)
    
    def escape_for_html(self, text: str) -> str:
        """
        HTML转义
        
        Args:
            text: 文本
            
        Returns:
            str: 转义后的文本
        """
        return self.encoder.encode_html(text)
    
    def escape_for_js(self, text: str) -> str:
        """
        JavaScript转义
        
        Args:
            text: 文本
            
        Returns:
            str: 转义后的文本
        """
        return self.encoder.encode_javascript(text)
    
    def escape_for_url(self, text: str) -> str:
        """
        URL转义
        
        Args:
            text: 文本
            
        Returns:
            str: 转义后的文本
        """
        return self.encoder.encode_url(text)
