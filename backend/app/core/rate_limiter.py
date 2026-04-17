"""
API限流器核心（Redis版本）

基于滑动窗口算法的API限流实现，符合三级等保要求：
- 8.1.3.1 边界防护：防止DoS攻击
- 8.1.3.4 入侵防范：API请求频率限制

数据存储策略：
- 临时数据（限流计数）→ Redis（Sorted Set + TTL自动过期）
- Redis不可用时 → 内存降级（线程安全字典）

Author: AI
Date: 2026-04-15
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
import threading


# 默认配置
DEFAULT_CONFIG = {
    "default_limit": 100,       # 默认每分钟100次
    "default_window": 60,       # 默认窗口60秒
    "enabled": True,            # 是否启用
    "block_duration": 60,       # 超出限制后阻塞时长（秒）
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
    滑动窗口限流器（Redis + 内存降级）
    
    优先使用 Redis Sorted Set 实现精确的分布式滑动窗口限流。
    Redis 不可用时自动降级为内存字典（单进程模式）。
    
    Redis 实现原理：
    - 使用 Sorted Set，score 为 Unix 时间戳
    - 每次请求 ZADD 添加当前时间戳
    - 查询时 ZREMRANGEBYSCORE 移除窗口外记录，ZCARD 获取计数
    - Key 设置 TTL = window * 2 自动过期
    """
    
    # Redis 键前缀
    REDIS_KEY_PREFIX = "ratelimit:"
    
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
            redis_client: Redis客户端实例（用于分布式限流）
        """
        self.default_limit = default_limit
        self.window = window
        self._redis = redis_client
        # 内存降级存储
        self._cache: Dict[str, list] = {}
        self._lock = threading.Lock()
    
    def _generate_key(
        self, 
        identifier: str, 
        path: str = "", 
        user_id: str = None
    ) -> str:
        """生成限流key"""
        if user_id:
            return f"{user_id}:{path}"
        return f"{identifier}:{path}"
    
    def _get_reset_time(self) -> int:
        """获取窗口重置时间（秒）"""
        now = time.time()
        window_start = (int(now) // self.window) * self.window
        next_window = window_start + self.window
        return max(1, int(next_window - now))
    
    # ==================== Redis 实现 ====================
    
    async def _redis_record_and_count(self, key: str) -> int:
        """
        Redis: 记录请求并返回窗口内计数
        
        使用 Sorted Set + 滑动窗口算法：
        1. 移除窗口外的旧记录
        2. 添加当前时间戳
        3. 返回当前计数
        """
        if self._redis is None:
            return -1
        
        try:
            r = await self._redis.connect()
            full_key = f"{self.REDIS_KEY_PREFIX}{key}"
            now = time.time()
            window_start = now - self.window
            
            pipe = r.pipeline(transaction=True)
            # 1. 移除窗口外的记录
            pipe.zremrangebyscore(full_key, 0, window_start)
            # 2. 添加当前请求
            pipe.zadd(full_key, {str(now): now})
            # 3. 获取当前计数
            pipe.zcard(full_key)
            # 4. 设置过期时间（窗口的2倍，确保安全）
            pipe.expire(full_key, self.window * 2)
            
            results = await pipe.execute()
            count = results[2]  # zcard 的结果
            return count
        except Exception:
            return -1
    
    async def _redis_get_count(self, key: str) -> int:
        """Redis: 获取窗口内当前计数（不记录新请求）"""
        if self._redis is None:
            return -1
        
        try:
            r = await self._redis.connect()
            full_key = f"{self.REDIS_KEY_PREFIX}{key}"
            now = time.time()
            window_start = now - self.window
            
            pipe = r.pipeline(transaction=True)
            pipe.zremrangebyscore(full_key, 0, window_start)
            pipe.zcard(full_key)
            
            results = await pipe.execute()
            return results[1]
        except Exception:
            return -1
    
    # ==================== 内存降级实现 ====================
    
    def _memory_record_and_count(self, key: str) -> int:
        """内存: 记录请求并返回窗口内计数"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window)
        
        with self._lock:
            if key not in self._cache:
                self._cache[key] = []
            
            self._cache[key].append(now)
            
            # 清理过期记录
            self._cache[key] = [t for t in self._cache[key] if t > cutoff]
            
            return len(self._cache[key])
    
    def _memory_get_count(self, key: str) -> int:
        """内存: 获取窗口内当前计数（不记录新请求）"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window)
        
        with self._lock:
            if key not in self._cache:
                return 0
            
            self._cache[key] = [t for t in self._cache[key] if t > cutoff]
            return len(self._cache[key])
    
    def _memory_get_remaining(self, key: str, limit: int) -> int:
        """内存: 获取剩余请求次数"""
        count = self._memory_get_count(key)
        return max(0, limit - count)
    
    # ==================== 公共接口 ====================
    
    async def is_allowed(self, key: str, limit: int = None) -> bool:
        """
        检查是否允许请求（异步版本）
        
        优先使用 Redis，失败时降级为内存
        """
        if limit is None:
            limit = self.default_limit
        
        if not DEFAULT_CONFIG["enabled"]:
            return True
        
        # 尝试 Redis
        count = await self._redis_record_and_count(key)
        if count >= 0:
            return count <= limit
        
        # 降级到内存
        count = self._memory_record_and_count(key)
        return count <= limit
    
    async def check_rate_limit(
        self, 
        key: str, 
        limit: int = None
    ) -> RateLimitResult:
        """
        检查限流并返回详细信息（异步版本）
        
        优先使用 Redis，失败时降级为内存
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
        
        reset_in = self._get_reset_time()
        
        # 尝试 Redis
        count = await self._redis_record_and_count(key)
        if count >= 0:
            remaining = max(0, limit - count)
            if count > limit:
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
        
        # 降级到内存
        count = self._memory_record_and_count(key)
        remaining = max(0, limit - count)
        if count > limit:
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
        """清理过期的内存缓存记录（仅用于内存降级模式）"""
        if max_age_seconds is None:
            max_age_seconds = self.window * 2
        
        with self._lock:
            cutoff = datetime.now() - timedelta(seconds=max_age_seconds)
            keys_to_remove = []
            
            for key, timestamps in self._cache.items():
                self._cache[key] = [t for t in timestamps if t > cutoff]
                if not self._cache[key]:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._cache[key]
            
            return len(keys_to_remove)
    
    def reset(self, key: str = None) -> None:
        """重置限流记录（仅内存模式，Redis 由 TTL 自动过期）"""
        with self._lock:
            if key is None:
                self._cache.clear()
            elif key in self._cache:
                del self._cache[key]
    
    def get_stats(self) -> dict:
        """获取限流统计信息"""
        with self._lock:
            return {
                "total_keys": len(self._cache),
                "total_requests": sum(len(v) for v in self._cache.values()),
                "default_limit": self.default_limit,
                "window": self.window,
                "enabled": DEFAULT_CONFIG["enabled"],
                "storage": "redis" if self._redis else "memory",
            }


# 全局限流器实例
_global_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    获取全局限流器实例（同步，内存模式）
    
    Redis 客户端需要在启动时通过 set_redis_client 注入
    """
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = RateLimiter(
            default_limit=DEFAULT_CONFIG["default_limit"],
            window=DEFAULT_CONFIG["default_window"],
        )
    return _global_limiter


def set_rate_limiter_redis(redis_client):
    """
    为全局限流器注入 Redis 客户端
    
    应在应用启动（lifespan）中调用
    """
    global _global_limiter
    limiter = get_rate_limiter()
    limiter._redis = redis_client
