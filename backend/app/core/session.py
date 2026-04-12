"""
会话超时管理器

提供会话管理和超时控制，符合三级等保要求：
- 8.1.2.2 访问控制：会话超时管理

Author: AI
Date: 2026-04-11
"""

import time
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from dataclasses import dataclass, field
import threading


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
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "remaining_seconds": self.remaining_seconds,
        }


class SessionManager:
    """
    会话管理器
    
    提供会话的创建、验证、刷新、销毁等功能。
    
    Attributes:
        redis_client: 可选的Redis客户端
        default_timeout: 默认超时时间
        absolute_timeout: 绝对超时时间
    """
    
    def __init__(
        self,
        redis_client=None,
        default_timeout: int = None,
        absolute_timeout: int = None,
    ):
        """
        初始化会话管理器
        
        Args:
            redis_client: Redis客户端（用于分布式）
            default_timeout: 默认超时时间
            absolute_timeout: 绝对超时时间
        """
        self.redis_client = redis_client
        self.default_timeout = default_timeout or SessionConfig.DEFAULT_TIMEOUT
        self.absolute_timeout = absolute_timeout or SessionConfig.ABSOLUTE_TIMEOUT
        
        # 内存缓存（单机部署）
        self._sessions: Dict[str, Session] = {}
        self._lock = threading.Lock()
    
    def _generate_session_id(self) -> str:
        """生成会话ID"""
        return secrets.token_hex(SessionConfig.SESSION_ID_LENGTH)
    
    def create_session(
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
        
        with self._lock:
            self._sessions[session_id] = session
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Session]: 会话对象
        """
        with self._lock:
            session = self._sessions.get(session_id)
            
            if session is None:
                return None
            
            # 检查过期
            if session.is_expired:
                self.destroy_session(session_id)
                return None
            
            # 检查是否激活
            if not session.is_active:
                return None
            
            return session
    
    def verify_session(self, session_id: str) -> bool:
        """
        验证会话有效性
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 会话是否有效
        """
        session = self.get_session(session_id)
        return session is not None
    
    def refresh_session(self, session_id: str) -> bool:
        """
        刷新会话超时
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功
        """
        session = self.get_session(session_id)
        if session is None:
            return False
        
        session.refresh()
        
        with self._lock:
            self._sessions[session_id] = session
        
        return True
    
    def destroy_session(self, session_id: str) -> bool:
        """
        销毁会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
        return False
    
    def destroy_user_sessions(self, user_id: str) -> int:
        """
        销毁用户的所有会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 销毁的会话数量
        """
        with self._lock:
            sessions_to_remove = [
                sid for sid, session in self._sessions.items()
                if session.user_id == user_id
            ]
            
            for sid in sessions_to_remove:
                del self._sessions[sid]
            
            return len(sessions_to_remove)
    
    def cleanup_expired_sessions(self) -> int:
        """
        清理过期会话
        
        Returns:
            int: 清理的会话数量
        """
        with self._lock:
            expired_sessions = [
                sid for sid, session in self._sessions.items()
                if session.is_expired or not session.is_active
            ]
            
            for sid in expired_sessions:
                del self._sessions[sid]
            
            return len(expired_sessions)
    
    def get_user_session_count(self, user_id: str) -> int:
        """
        获取用户的会话数量
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 会话数量
        """
        with self._lock:
            return sum(
                1 for session in self._sessions.values()
                if session.user_id == user_id and not session.is_expired
            )
    
    def get_stats(self) -> dict:
        """
        获取会话统计
        
        Returns:
            dict: 统计信息
        """
        with self._lock:
            total = len(self._sessions)
            active = sum(
                1 for s in self._sessions.values()
                if s.is_active and not s.is_expired
            )
            expired = total - active
            
            return {
                "total_sessions": total,
                "active_sessions": active,
                "expired_sessions": expired,
                "default_timeout_seconds": self.default_timeout,
                "absolute_timeout_seconds": self.absolute_timeout,
            }


# 全局会话管理器
_global_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    获取全局会话管理器
    
    Returns:
        SessionManager: 会话管理器实例
    """
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = SessionManager()
    return _global_session_manager
