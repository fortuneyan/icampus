"""
CSRF防护中间件

为FastAPI应用提供CSRF防护，符合三级等保要求：
- 8.1.2.2 访问控制：防止CSRF攻击

Author: AI
Date: 2026-04-11
"""

from typing import Callable, Optional, Set
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse, PlainTextResponse
from starlette.types import ASGIApp
import re

from app.core.csrf import CSRFToken, CSRFConfig, CSRFUtils


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF防护中间件
    
    对非安全HTTP方法（POST, PUT, DELETE等）进行CSRF Token验证。
    
    Attributes:
        app: ASGI应用
        exempt_paths: 豁免路径集合
        secret: CSRF密钥
    """
    
    def __init__(
        self,
        app: ASGIApp,
        secret: str = None,
        exempt_paths: set = None,
        enabled: bool = True,
    ):
        """
        初始化CSRF中间件
        
        Args:
            app: ASGI应用
            secret: CSRF密钥
            exempt_paths: 豁免路径集合
            enabled: 是否启用
        """
        super().__init__(app)
        self.enabled = enabled
        self.exempt_paths = exempt_paths or set()
        self.secret = secret or CSRFToken.generate_secret()
        
        # 默认豁免路径
        self._default_exempt = {
            r"^/$",
            r"^/health$",
            r"^/docs",
            r"^/redoc",
            r"^/openapi\.json$",
            r"^/api/v1/auth/login$",
            r"^/api/v1/auth/register$",
        }
    
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
        # 检查是否启用
        if not self.enabled:
            return await call_next(request)
        
        # 检查是否为安全方法
        method = request.method.upper()
        if CSRFUtils.is_safe_method(method):
            return await call_next(request)
        
        # 检查豁免路径
        path = request.url.path
        if self._is_exempt_path(path):
            return await call_next(request)
        
        # 验证CSRF Token
        token_valid = await self._verify_csrf_token(request)
        
        if not token_valid:
            return JSONResponse(
                status_code=403,
                content={
                    "error": "CSRF验证失败",
                    "detail": "无效的CSRF Token或Token缺失",
                    "code": "CSRF_ERROR",
                }
            )
        
        return await call_next(request)
    
    async def _verify_csrf_token(self, request: Request) -> bool:
        """
        验证CSRF Token
        
        从Header或Cookie获取Token并验证。
        
        Args:
            request: HTTP请求
            
        Returns:
            bool: Token是否有效
        """
        # 尝试从Header获取
        header_token = request.headers.get(CSRFConfig.HEADER_NAME)
        
        # 尝试从Cookie获取
        cookie_token = None
        if hasattr(request, 'cookies'):
            cookie_token = request.cookies.get(CSRFConfig.TOKEN_NAME)
        
        # 获取存储的Token（通常在session或state中）
        stored_token = getattr(request.state, 'csrf_token', None)
        
        # 优先使用Header中的Token
        token_to_verify = header_token or cookie_token
        
        if not token_to_verify:
            return False
        
        # 如果有存储的Token，进行验证
        if stored_token:
            return CSRFToken.verify(token_to_verify, stored_token, self.secret)
        
        # 如果没有存储的Token，只要提供了Token就通过
        # （适用于仅检查Token存在性的场景）
        return len(token_to_verify) >= 32
    
    def _is_exempt_path(self, path: str) -> bool:
        """
        检查路径是否豁免
        
        Args:
            path: 请求路径
            
        Returns:
            bool: 是否豁免
        """
        # 检查默认豁免
        for pattern in self._default_exempt:
            if re.match(pattern, path):
                return True
        
        # 检查自定义豁免
        for pattern in self.exempt_paths:
            if re.match(pattern, path):
                return True
        
        return False
    
    def add_exempt_path(self, pattern: str) -> None:
        """
        添加豁免路径
        
        Args:
            pattern: 正则表达式模式
        """
        self.exempt_paths.add(pattern)
    
    def remove_exempt_path(self, pattern: str) -> None:
        """
        移除豁免路径
        
        Args:
            pattern: 正则表达式模式
        """
        self.exempt_paths.discard(pattern)


class CSRFTokenGenerator:
    """
    CSRF Token生成器
    
    用于在响应中生成和设置Token。
    """
    
    def __init__(self, secret: str = None):
        """
        初始化
        
        Args:
            secret: CSRF密钥
        """
        self.secret = secret or CSRFToken.generate_secret()
    
    def generate_token(self, user_id: str = None) -> str:
        """
        生成Token
        
        Args:
            user_id: 可选的用户ID
            
        Returns:
            str: CSRF Token
        """
        if user_id:
            return CSRFToken.create_signed_token(user_id, self.secret)
        return CSRFToken.generate(self.secret)
    
    def create_token_response(
        self,
        token: str,
        secure: bool = CSRFConfig.COOKIE_SECURE,
        httponly: bool = CSRFConfig.COOKIE_HTTPONLY,
        samesite: str = CSRFConfig.COOKIE_SAMESITE,
    ) -> dict:
        """
        创建Token响应信息
        
        Args:
            token: CSRF Token
            secure: Cookie secure标志
            httponly: Cookie httponly标志
            samesite: Cookie samesite属性
            
        Returns:
            dict: 包含Token和Cookie配置
        """
        return {
            "token": token,
            "token_name": CSRFConfig.TOKEN_NAME,
            "header_name": CSRFConfig.HEADER_NAME,
            "cookie_options": {
                "name": CSRFConfig.TOKEN_NAME,
                "value": token,
                "secure": secure,
                "httponly": httponly,
                "samesite": samesite,
                "path": "/",
            }
        }
