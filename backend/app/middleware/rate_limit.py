"""
API限流中间件

为FastAPI应用提供限流功能的中间件，符合三级等保要求：
- 8.1.3.1 边界防护：防止DoS攻击
- 8.1.3.4 入侵防范：API请求频率限制

Author: AI
Date: 2026-04-11
"""

from typing import Callable, Optional, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp
import re

from app.core.rate_limiter import (
    RateLimiter,
    get_rate_limiter,
    ENDPOINT_CONFIGS,
    WHITELIST,
    RATE_LIMIT_MESSAGE,
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    API限流中间件
    
    对API请求进行频率限制，支持：
    - 按IP限流
    - 按用户ID限流
    - 按端点类型限流
    - IP白名单
    
    Attributes:
        app: ASGI应用
        limiter: 限流器实例
        whitelist: IP白名单
    """
    
    def __init__(
        self,
        app: ASGIApp,
        limiter: RateLimiter = None,
        whitelist: list = None,
        enabled: bool = True,
    ):
        """
        初始化限流中间件
        
        Args:
            app: ASGI应用
            limiter: 限流器实例
            whitelist: IP白名单
            enabled: 是否启用限流
        """
        super().__init__(app)
        self.limiter = limiter or get_rate_limiter()
        self.whitelist = whitelist or WHITELIST
        self.enabled = enabled
        self._exempt_paths = [
            r"^/$",
            r"^/health$",
            r"^/docs",
            r"^/redoc",
            r"^/openapi\.json$",
        ]
    
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
        
        # 检查豁免路径
        path = request.url.path
        if self._is_exempt_path(path):
            return await call_next(request)
        
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        # 检查白名单
        if self._is_whitelisted(client_ip):
            return await call_next(request)
        
        # 获取限流配置
        limit, window = self._get_rate_limit_for_path(path)
        
        # 生成限流key
        key = self._generate_key(request, client_ip)
        
        # 检查限流（异步，支持 Redis 后端）
        result = await self.limiter.check_rate_limit(key, limit)
        
        # 构建响应头
        headers = self._build_headers(
            limit=result.limit,
            remaining=result.remaining,
            reset_in=result.reset_in,
        )
        
        # 如果被限流，返回429
        if not result.allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": RATE_LIMIT_MESSAGE,
                    "detail": f"请求过于频繁，请在 {result.retry_after} 秒后重试",
                    "code": "RATE_LIMIT_EXCEEDED",
                },
                headers={
                    **headers,
                    "Retry-After": str(result.retry_after),
                },
            )
        
        # 执行请求
        response = await call_next(request)
        
        # 添加限流响应头
        for key, value in headers.items():
            response.headers[key] = value
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端真实IP
        
        优先从X-Forwarded-For获取，其次从X-Real-IP，最后从client.host
        
        Args:
            request: HTTP请求
            
        Returns:
            str: 客户端IP
        """
        # 优先从代理头获取
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # 取第一个IP（最原始的客户端）
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # 直接从连接获取
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _is_whitelisted(self, ip: str) -> bool:
        """
        检查IP是否在白名单中
        
        Args:
            ip: 客户端IP
            
        Returns:
            bool: 是否在白名单
        """
        return ip in self.whitelist
    
    def _is_exempt_path(self, path: str) -> bool:
        """
        检查路径是否豁免限流
        
        Args:
            path: 请求路径
            
        Returns:
            bool: 是否豁免
        """
        for pattern in self._exempt_paths:
            if re.match(pattern, path):
                return True
        return False
    
    def _get_rate_limit_for_path(self, path: str) -> Tuple[int, int]:
        """
        根据路径获取限流配置
        
        Args:
            path: 请求路径
            
        Returns:
            Tuple[int, int]: (限制次数, 窗口秒数)
        """
        path_lower = path.lower()
        
        # 登录接口
        if "login" in path_lower or "signin" in path_lower:
            config = ENDPOINT_CONFIGS["login"]
            return config["limit"], config["window"]
        
        # 注册接口
        if "register" in path_lower or "signup" in path_lower:
            config = ENDPOINT_CONFIGS["register"]
            return config["limit"], config["window"]
        
        # 密码重置
        if "password" in path_lower or "reset" in path_lower:
            config = ENDPOINT_CONFIGS["password_reset"]
            return config["limit"], config["window"]
        
        # API接口
        if path.startswith("/api/"):
            config = ENDPOINT_CONFIGS["api"]
            return config["limit"], config["window"]
        
        # 默认配置
        config = ENDPOINT_CONFIGS["default"]
        return config["limit"], config["window"]
    
    def _generate_key(self, request: Request, ip: str) -> str:
        """
        生成限流key
        
        Args:
            request: HTTP请求
            ip: 客户端IP
            
        Returns:
            str: 限流key
        """
        path = request.url.path
        
        # 尝试从请求中获取用户ID（如果已认证）
        user_id = getattr(request.state, "user_id", None)
        
        if user_id:
            return f"{user_id}:{path}"
        
        return f"{ip}:{path}"
    
    def _build_headers(
        self, 
        limit: int, 
        remaining: int, 
        reset_in: int
    ) -> dict:
        """
        构建限流响应头
        
        Args:
            limit: 限制次数
            remaining: 剩余次数
            reset_in: 重置时间（秒）
            
        Returns:
            dict: 响应头字典
        """
        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_in),
            "X-RateLimit-Window": "60",
        }
    
    def add_exempt_path(self, pattern: str) -> None:
        """
        添加豁免路径
        
        Args:
            pattern: 正则表达式模式
        """
        self._exempt_paths.append(pattern)
    
    def remove_exempt_path(self, pattern: str) -> None:
        """
        移除豁免路径
        
        Args:
            pattern: 正则表达式模式
        """
        if pattern in self._exempt_paths:
            self._exempt_paths.remove(pattern)
    
    def add_whitelist(self, ip: str) -> None:
        """
        添加白名单IP
        
        Args:
            ip: IP地址
        """
        if ip not in self.whitelist:
            self.whitelist.append(ip)
    
    def remove_whitelist(self, ip: str) -> None:
        """
        移除白名单IP
        
        Args:
            ip: IP地址
        """
        if ip in self.whitelist:
            self.whitelist.remove(ip)
