"""
Redis客户端管理模块

提供统一的Redis连接管理和数据访问接口
支持数据分层存储策略：
- 临时数据：会话、限流计数、缓存（TTL自动过期）
- 实时数据：仅在内存中，不持久化

Author: AI
Date: 2026-04-15
"""

import pickle
from typing import Optional, Any, Dict
import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings


class RedisClient:
    """Redis客户端封装"""
    
    _instance: Optional['RedisClient'] = None
    _redis: Optional[Redis] = None
    
    # 键前缀命名空间
    KEY_PREFIX = {
        "session": "sess:",           # 用户会话
        "rate_limit": "ratelimit:",   # 限流计数
        "cache": "cache:",            # 通用缓存
        "temp": "temp:",              # 临时数据
    }
    
    # 默认TTL配置（秒）
    DEFAULT_TTL = {
        "session": 30 * 60,           # 会话：30分钟
        "rate_limit": 120,            # 限流：2分钟
        "cache": 300,                 # 缓存：5分钟
        "temp": 600,                  # 临时：10分钟
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self) -> Redis:
        """建立Redis连接"""
        if self._redis is None:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self._redis = await redis.from_url(
                redis_url,
                encoding='utf-8',
                decode_responses=False,
                max_connections=50,
            )
        return self._redis
    
    async def disconnect(self):
        """关闭Redis连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    def _make_key(self, key: str, prefix: str) -> str:
        """生成带前缀的键名"""
        prefix_str = self.KEY_PREFIX.get(prefix, "")
        return f"{prefix_str}{key}"
    
    def _serialize(self, value: Any) -> bytes:
        """序列化数据"""
        if isinstance(value, (str, bytes)):
            return value.encode() if isinstance(value, str) else value
        return pickle.dumps(value)
    
    def _deserialize(self, value: bytes) -> Any:
        """反序列化数据"""
        if value is None:
            return None
        try:
            return pickle.loads(value)
        except:
            try:
                return value.decode('utf-8')
            except:
                return value
    
    async def get(self, key: str, prefix: str = "cache") -> Optional[Any]:
        """获取值"""
        r = await self.connect()
        full_key = self._make_key(key, prefix)
        value = await r.get(full_key)
        return self._deserialize(value) if value else None
    
    async def set(
        self, key: str, value: Any, prefix: str = "cache",
        ttl: Optional[int] = None, ttl_key: Optional[str] = None
    ) -> bool:
        """设置值"""
        r = await self.connect()
        full_key = self._make_key(key, prefix)
        if ttl is None and ttl_key:
            ttl = self.DEFAULT_TTL.get(ttl_key)
        serialized = self._serialize(value)
        if ttl:
            await r.setex(full_key, ttl, serialized)
        else:
            await r.set(full_key, serialized)
        return True
    
    async def delete(self, key: str, prefix: str = "cache") -> bool:
        """删除键"""
        r = await self.connect()
        full_key = self._make_key(key, prefix)
        result = await r.delete(full_key)
        return result > 0
    
    async def exists(self, key: str, prefix: str = "cache") -> bool:
        """检查键是否存在"""
        r = await self.connect()
        full_key = self._make_key(key, prefix)
        return await r.exists(full_key) > 0
    
    async def expire(self, key: str, seconds: int, prefix: str = "cache") -> bool:
        """设置过期时间"""
        r = await self.connect()
        full_key = self._make_key(key, prefix)
        return await r.expire(full_key, seconds)
    
    async def ttl(self, key: str, prefix: str = "cache") -> int:
        """获取剩余过期时间"""
        r = await self.connect()
        full_key = self._make_key(key, prefix)
        return await r.ttl(full_key)
    
    # Hash操作
    async def hset(self, key: str, field: str, value: Any, 
                   prefix: str = "cache", ttl: Optional[int] = None) -> bool:
        """设置Hash字段"""
        r = await self.connect()
        full_key = self._make_key(key, prefix)
        await r.hset(full_key, field, self._serialize(value))
        if ttl:
            await r.expire(full_key, ttl)
        return True
    
    async def hget(self, key: str, field: str, prefix: str = "cache") -> Optional[Any]:
        """获取Hash字段"""
        r = await self.connect()
        full_key = self._make_key(key, prefix)
        value = await r.hget(full_key, field)
        return self._deserialize(value) if value else None
    
    async def hgetall(self, key: str, prefix: str = "cache") -> Dict[str, Any]:
        """获取所有Hash字段"""
        r = await self.connect()
        full_key = self._make_key(key, prefix)
        data = await r.hgetall(full_key)
        return {k.decode() if isinstance(k, bytes) else k: self._deserialize(v) 
                for k, v in data.items()}
    
    async def hdel(self, key: str, field: str, prefix: str = "cache") -> bool:
        """删除Hash字段"""
        r = await self.connect()
        full_key = self._make_key(key, prefix)
        result = await r.hdel(full_key, field)
        return result > 0
    
    async def hincrby(self, key: str, field: str, amount: int = 1, 
                      prefix: str = "cache") -> int:
        """Hash字段自增"""
        r = await self.connect()
        full_key = self._make_key(key, prefix)
        return await r.hincrby(full_key, field, amount)


# 全局Redis客户端实例
_redis_client: Optional[RedisClient] = None


async def get_redis_client() -> RedisClient:
    """获取Redis客户端实例"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client


async def close_redis_connection():
    """关闭Redis连接（应用关闭时调用）"""
    global _redis_client
    if _redis_client:
        await _redis_client.disconnect()
        _redis_client = None
