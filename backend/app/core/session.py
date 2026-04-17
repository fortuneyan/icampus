"""
会话超时管理器（Redis版本）

提供会话管理和超时控制，符合三级等保要求：
- 8.1.2.2 访问控制：会话超时管理

数据存储策略：
- 临时数据（会话信息）→ Redis（TTL自动过期）
- 仅实时计算状态 → 内存

Author: AI
Date: 2026-04-15
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict
import json

from app.core.redis_client import RedisClient, get_redis_client
from app.core.logger import logger


class SessionConfig:
    """会话配置"""
    
    # 默认超时时间（秒）
    DEFAULT_TIMEOUT = 30 * 60  # 30分钟
    
    # 绝对超时时间（秒）
    ABSOLUTE_TIMEOUT = 8 * 60 * 60  # 8小时
    
    # 会话ID长度
    SESSION_ID_LENGTH = 32
    
    # 是否启用绝对超时
    ENABLE_ABSOLUTE_TIMEOUT = True
    
    # 刷新时间（秒）- 活跃操作时刷新超时
    REFRESH_GRACE_PERIOD = 5 * 60  # 5分钟


@dataclass
class Session:
    """
    会话对象
    
    Attributes:
        session_id: 会话ID
        user_id: 用户ID
        created_at: 创建时间
        last_accessed: 最后访问时间
        expires_at: 过期时间
        is_active: 是否活跃
        ip_address: IP地址
        user_agent: 用户代理
        data: 会话数据
    """
    
    session_id: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    data: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if self.expires_at is None:
            self.expires_at = datetime.now() + timedelta(seconds=SessionConfig.DEFAULT_TIMEOUT)
    
    @property
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return datetime.now() > self.expires_at
    
    @property
    def remaining_seconds(self) -> int:
        """获取剩余时间（秒）"""
        remaining = (self.expires_at - datetime.now()).total_seconds()
        return max(0, int(remaining))
    
    def refresh(self) -> None:
        """刷新会话"""
        self.last_accessed = datetime.now()
        self.expires_at = datetime.now() + timedelta(seconds=SessionConfig.DEFAULT_TIMEOUT)
    
    def extend(self, additional_seconds: int) -> None:
        """延长会话"""
        self.expires_at = datetime.now() + timedelta(seconds=additional_seconds)
    
    def invalidate(self) -> None:
        """使会话失效"""
        self.is_active = False
        self.expires_at = datetime.now()
    
    def to_dict(self) -> dict:
        """转换为字典（用于Redis存储）"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "data": self.data,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """从字典创建会话对象"""
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            is_active=data.get("is_active", True),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            data=data.get("data", {}),
        )


class SessionManager:
    """
    会话管理器（Redis版本）
    
    提供会话的创建、验证、刷新、销毁等功能。
    会话数据存储在Redis中，支持分布式部署。
    
    Attributes:
        redis_client: Redis客户端
        default_timeout: 默认超时时间
        absolute_timeout: 绝对超时时间
    """
    
    # Redis键前缀
    KEY_PREFIX = "session:"
    USER_SESSIONS_PREFIX = "user_sessions:"
    
    def __init__(
        self,
        redis_client: Optional[RedisClient] = None,
        default_timeout: int = None,
        absolute_timeout: int = None,
    ):
        """
        初始化会话管理器
        
        Args:
            redis_client: Redis客户端
            default_timeout: 默认超时时间
            absolute_timeout: 绝对超时时间
        """
        self._redis = redis_client
        self.default_timeout = default_timeout or SessionConfig.DEFAULT_TIMEOUT
        self.absolute_timeout = absolute_timeout or SessionConfig.ABSOLUTE_TIMEOUT
    
    async def _get_redis(self) -> Optional[RedisClient]:
        """获取Redis客户端"""
        if self._redis is None:
            try:
                self._redis = await get_redis_client()
            except Exception as e:
                logger.error(f"获取Redis客户端失败: {e}")
                return None
        return self._redis
    
    def _make_key(self, session_id: str) -> str:
        """生成Redis键名"""
        return f"{self.KEY_PREFIX}{session_id}"
    
    def _make_user_key(self, user_id: str) -> str:
        """生成用户会话集合键名"""
        return f"{self.USER_SESSIONS_PREFIX}{user_id}"
    
    def _generate_session_id(self) -> str:
        """生成会话ID"""
        return secrets.token_hex(SessionConfig.SESSION_ID_LENGTH)
    
    async def create_session(
        self,
        user_id: str,
        ip_address: str = None,
        user_agent: str = None,
        data: dict = None,
    ) -> Session:
        """
        创建新会话
        
        Args:
            user_id: 用户ID
            ip_address: IP地址
            user_agent: 用户代理
            data: 会话数据
            
        Returns:
            Session: 新创建的会话
        """
        session_id = self._generate_session_id()
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            data=data or {},
        )
        
        # 设置过期时间
        session.expires_at = datetime.now() + timedelta(seconds=self.default_timeout)
        
        # 存储到Redis
        redis = await self._get_redis()
        if redis:
            session_key = self._make_key(session_id)
            user_key = self._make_user_key(user_id)
            
            await redis.set(
                session_key,
                session.to_dict(),
                prefix="",
                ttl=self.default_timeout
            )
            # 将会话ID添加到用户的会话集合
            await redis.hset(user_key, session_id, datetime.now().isoformat(), prefix="", ttl=self.absolute_timeout)
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Session]: 会话对象
        """
        redis = await self._get_redis()
        if not redis:
            return None
        
        session_key = self._make_key(session_id)
        data = await redis.get(session_key, prefix="")
        
        if not data:
            return None
        
        try:
            session = Session.from_dict(data)
        except Exception as e:
            logger.error(f"解析会话数据失败: {e}")
            return None
        
        # 检查过期
        if session.is_expired or not session.is_active:
            await self.destroy_session(session_id)
            return None
        
        return session
    
    async def verify_session(self, session_id: str) -> bool:
        """
        验证会话有效性
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 会话是否有效
        """
        session = await self.get_session(session_id)
        return session is not None
    
    async def refresh_session(self, session_id: str) -> bool:
        """
        刷新会话超时
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功
        """
        session = await self.get_session(session_id)
        if session is None:
            return False
        
        session.refresh()
        
        # 更新Redis
        redis = await self._get_redis()
        if redis:
            session_key = self._make_key(session_id)
            await redis.set(
                session_key,
                session.to_dict(),
                prefix="",
                ttl=self.default_timeout
            )
        
        return True
    
    async def destroy_session(self, session_id: str) -> bool:
        """
        销毁会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功
        """
        redis = await self._get_redis()
        if not redis:
            return False
        
        # 获取会话以找到用户ID
        session = await self.get_session(session_id)
        
        session_key = self._make_key(session_id)
        result = await redis.delete(session_key, prefix="")
        
        # 从用户的会话集合中移除
        if session:
            user_key = self._make_user_key(session.user_id)
            await redis.hdel(user_key, session_id, prefix="")
        
        return result
    
    async def destroy_user_sessions(self, user_id: str) -> int:
        """
        销毁用户的所有会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 销毁的会话数量
        """
        redis = await self._get_redis()
        if not redis:
            return 0
        
        user_key = self._make_user_key(user_id)
        sessions_data = await redis.hgetall(user_key, prefix="")
        
        count = 0
        for session_id in sessions_data.keys():
            session_key = self._make_key(session_id)
            if await redis.delete(session_key, prefix=""):
                count += 1
        
        # 删除用户的会话集合
        await redis.delete(user_key, prefix="")
        
        return count
    
    async def cleanup_expired_sessions(self) -> int:
        """
        清理过期会话（Redis自动过期，此方法主要用于统计）
        
        Returns:
            int: 清理的会话数量（估算）
        """
        # Redis会自动过期，这里返回0
        # 实际清理由Redis的TTL机制处理
        return 0
    
    async def get_user_session_count(self, user_id: str) -> int:
        """
        获取用户的会话数量
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 会话数量
        """
        redis = await self._get_redis()
        if not redis:
            return 0
        
        user_key = self._make_user_key(user_id)
        sessions_data = await redis.hgetall(user_key, prefix="")
        
        # 验证每个会话是否仍然有效
        valid_count = 0
        for session_id in sessions_data.keys():
            if await self.verify_session(session_id):
                valid_count += 1
        
        return valid_count
    
    async def get_stats(self) -> dict:
        """
        获取会话统计
        
        Returns:
            dict: 统计信息
        """
        # Redis版本无法直接获取所有会话统计
        # 返回配置信息
        return {
            "total_sessions": -1,  # 无法准确统计
            "active_sessions": -1,
            "expired_sessions": -1,
            "default_timeout_seconds": self.default_timeout,
            "absolute_timeout_seconds": self.absolute_timeout,
            "storage": "redis",
        }


# 全局会话管理器
_global_session_manager: Optional[SessionManager] = None


async def get_session_manager() -> SessionManager:
    """
    获取全局会话管理器
    
    Returns:
        SessionManager: 会话管理器实例
    """
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = SessionManager()
    return _global_session_manager


def get_session_manager_sync() -> SessionManager:
    """
    同步获取全局会话管理器（用于非异步上下文）
    
    Returns:
        SessionManager: 会话管理器实例
    """
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = SessionManager()
    return _global_session_manager
