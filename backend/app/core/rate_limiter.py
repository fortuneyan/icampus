"""
API限流器核心

基于滑动窗口算法的API限流实现，符合三级等保要求：
- 8.1.3.1 边界防护：防止DoS攻击
- 8.1.3.4 入侵防范：API请求频率限制

Author: AI
Date: 2026-04-11
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
import threading


# 默认配置
DEFAULT_CONFIG = {
    "default_limit": 100,       # 默认每分钟100次
    "default_window": 60,       # 默认窗口60秒
    "enabled": True,            # 是否启用
    "block_duration": 60,      # 超出限制后阻塞时长（秒）
}

# 端点配置
ENDPOINT_CONFIGS = {
    "login": {"limit": 10, "window": 60, "description": "登录接口"},
    "register": {"limit": 5, "window": 300, "description": "注册接口"},
    "password_reset": {"limit": 3, "window": 300, "description": "密码重置"},
    "api": {"limit": 60, "window": 60, "description": "普通API"},
    "default": {"limit": 100, "window": 60, "description": "默认配置"},
}

# 白名单（管理员IP等）
WHITELIST = [
    "127.0.0.1",
    "localhost",
]

# 响应消息
RATE_LIMIT_MESSAGE = "请求过于频繁，请稍后再试"


@dataclass
class RateLimitResult:
    """限流检查结果"""
    allowed: bool          # 是否允许请求
    limit: int            # 限制次数
    remaining: int        # 剩余次数
    reset_in: int         # 多少秒后重置
    retry_after: Optional[int] = None  # 重试间隔（秒）


class RateLimiter:
    """
    滑动窗口限流器
    
    使用滑动窗口算法实现精确的请求频率限制。
    
    Attributes:
        default_limit: 默认限制次数
        window: 时间窗口（秒）
        _cache: 请求记录缓存
        _lock: 线程锁
    """
    
    def __init__(
        self, 
        default_limit: int = 100, 
        window: int = 60,
        redis_client = None
    ):
        """
        初始化限流器
        
        Args:
            default_limit: 默认限制次数（窗口内）
            window: 时间窗口（秒）
            redis_client: 可选的Redis客户端（用于分布式限流）
        """
        self.default_limit = default_limit
        self.window = window
        self.redis_client = redis_client
        self._cache: Dict[str, list] = {}  # key -> [timestamp1, timestamp2, ...]
        self._lock = threading.Lock()
    
    def _generate_key(
        self, 
        identifier: str, 
        path: str = "", 
        user_id: str = None
    ) -> str:
        """
        生成限流key
        
        Args:
            identifier: 标识符（通常是IP）
            path: 请求路径
            user_id: 可选的用户ID
            
        Returns:
            str: 限流key
        """
        if user_id:
            return f"{user_id}:{path}"
        return f"{identifier}:{path}"
    
    def _get_window_start(self, dt: datetime = None) -> datetime:
        """
        获取当前时间窗口的开始时间
        
        Args:
            dt: 可选的时间，默认为当前时间
            
        Returns:
            datetime: 窗口开始时间
        """
        if dt is None:
            dt = datetime.now()
        # 向下取整到窗口边界
        seconds = int(dt.timestamp())
        window_seconds = (seconds // self.window) * self.window
        return datetime.fromtimestamp(window_seconds)
    
    def _record_request(self, key: str, timestamp: datetime = None) -> int:
        """
        记录请求并返回当前窗口内请求数
        
        Args:
            key: 限流key
            timestamp: 请求时间
            
        Returns:
            int: 当前窗口内的请求数
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        with self._lock:
            if key not in self._cache:
                self._cache[key] = []
            
            # 添加时间戳
            self._cache[key].append(timestamp)
            
            # 清理过期记录
            window_start = self._get_window_start(timestamp)
            cutoff = window_start - timedelta(seconds=self.window)
            self._cache[key] = [
                t for t in self._cache[key] 
                if t > cutoff
            ]
            
            return len(self._cache[key])
    
    def _get_remaining(self, key: str, limit: int) -> int:
        """
        获取剩余请求次数
        
        Args:
            key: 限流key
            limit: 限制次数
            
        Returns:
            int: 剩余请求次数
        """
        with self._lock:
            if key not in self._cache:
                return limit
            
            window_start = self._get_window_start()
            cutoff = window_start - timedelta(seconds=self.window)
            
            # 计算有效请求数
            valid_requests = [
                t for t in self._cache[key] 
                if t > cutoff
            ]
            
            self._cache[key] = valid_requests
            current = len(valid_requests)
            
            return max(0, limit - current)
    
    def _get_reset_time(self) -> int:
        """
        获取窗口重置时间
        
        Returns:
            int: 距离窗口重置的秒数
        """
        now = datetime.now()
        window_start = self._get_window_start(now)
        next_window = window_start + timedelta(seconds=self.window)
        reset_timestamp = int(next_window.timestamp())
        current_timestamp = int(now.timestamp())
        return max(1, reset_timestamp - current_timestamp)
    
    def is_allowed(self, key: str, limit: int = None) -> bool:
        """
        检查是否允许请求
        
        Args:
            key: 限流key
            limit: 限制次数
            
        Returns:
            bool: 是否允许请求
        """
        if limit is None:
            limit = self.default_limit
        
        if not DEFAULT_CONFIG["enabled"]:
            return True
        
        current_count = self._record_request(key)
        
        if current_count > limit:
            return False
        
        return True
    
    def check_rate_limit(
        self, 
        key: str, 
        limit: int = None
    ) -> RateLimitResult:
        """
        检查限流并返回详细信息
        
        Args:
            key: 限流key
            limit: 限制次数
            
        Returns:
            RateLimitResult: 限流检查结果
        """
        if limit is None:
            limit = self.default_limit
        
        if not DEFAULT_CONFIG["enabled"]:
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=limit,
                reset_in=self.window,
            )
        
        current_count = self._record_request(key)
        remaining = max(0, limit - current_count)
        reset_in = self._get_reset_time()
        
        if current_count > limit:
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_in=reset_in,
                retry_after=reset_in,
            )
        
        return RateLimitResult(
            allowed=True,
            limit=limit,
            remaining=remaining,
            reset_in=reset_in,
        )
    
    def _cleanup_expired(self, max_age_seconds: int = None) -> int:
        """
        清理过期的缓存记录
        
        Args:
            max_age_seconds: 最大保留时间（秒），默认为2个窗口
            
        Returns:
            int: 清理的key数量
        """
        if max_age_seconds is None:
            max_age_seconds = self.window * 2
        
        with self._lock:
            cutoff = datetime.now() - timedelta(seconds=max_age_seconds)
            keys_to_remove = []
            
            for key, timestamps in self._cache.items():
                # 清理过期时间戳
                self._cache[key] = [t for t in timestamps if t > cutoff]
                
                # 如果没有有效记录，标记删除
                if not self._cache[key]:
                    keys_to_remove.append(key)
            
            # 删除空记录
            for key in keys_to_remove:
                del self._cache[key]
            
            return len(keys_to_remove)
    
    def reset(self, key: str = None) -> None:
        """
        重置限流记录
        
        Args:
            key: 限流key，为None则重置所有
        """
        with self._lock:
            if key is None:
                self._cache.clear()
            elif key in self._cache:
                del self._cache[key]
    
    def get_stats(self) -> dict:
        """
        获取限流统计信息
        
        Returns:
            dict: 统计信息
        """
        with self._lock:
            return {
                "total_keys": len(self._cache),
                "total_requests": sum(len(v) for v in self._cache.values()),
                "default_limit": self.default_limit,
                "window": self.window,
                "enabled": DEFAULT_CONFIG["enabled"],
            }


# 全局限流器实例
_global_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    获取全局限流器实例
    
    Returns:
        RateLimiter: 限流器实例
    """
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = RateLimiter(
            default_limit=DEFAULT_CONFIG["default_limit"],
            window=DEFAULT_CONFIG["default_window"],
        )
    return _global_limiter
