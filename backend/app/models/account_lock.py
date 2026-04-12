"""
账户锁定模型

记录用户登录失败导致的账户锁定信息，符合三级等保要求：
- 8.1.2.1 身份鉴别：登录失败处理
- 连续多次失败应锁定账户

Author: AI
Date: 2026-04-11
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from dataclasses import dataclass, field


@dataclass
class AccountLock:
    """
    账户锁定记录
    
    用于记录因连续登录失败而被锁定的账户信息。
    
    Attributes:
        id: 锁定记录ID
        user_id: 被锁定的用户ID
        lock_reason: 锁定原因
        failed_attempts: 失败尝试次数
        locked_at: 锁定开始时间
        unlock_at: 解锁时间
        is_auto_unlock: 是否自动解锁
        unlocked_by: 解锁管理员ID
        unlocked_at: 实际解锁时间
        created_at: 记录创建时间
        updated_at: 记录更新时间
    """
    
    user_id: uuid4
    lock_reason: str = "连续登录失败"
    failed_attempts: int = 0
    locked_at: Optional[datetime] = None
    unlock_at: Optional[datetime] = None
    is_auto_unlock: bool = True
    unlocked_by: Optional[uuid4] = None
    unlocked_at: Optional[datetime] = None
    id: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """初始化后处理"""
        if self.locked_at is None and self.unlock_at is not None:
            self.locked_at = datetime.now()
    
    @property
    def is_locked(self) -> bool:
        """
        检查账户是否仍处于锁定状态
        
        Returns:
            bool: 如果当前时间未超过解锁时间则返回True
        """
        if self.unlock_at is None:
            return False
        return datetime.now() < self.unlock_at
    
    @property
    def is_auto_unlock(self) -> bool:
        """是否自动解锁"""
        return self._is_auto_unlock
    
    @is_auto_unlock.setter
    def is_auto_unlock(self, value: bool):
        """设置是否自动解锁"""
        self._is_auto_unlock = value
    
    def get_remaining_lock_seconds(self) -> int:
        """
        获取剩余锁定秒数
        
        Returns:
            int: 剩余锁定时间（秒），已过期返回0
        """
        if self.unlock_at is None:
            return 0
        
        remaining = (self.unlock_at - datetime.now()).total_seconds()
        return max(0, int(remaining))
    
    def get_lock_duration_minutes(self) -> int:
        """
        获取锁定持续时间（分钟）
        
        Returns:
            int: 锁定持续时间（分钟）
        """
        if self.locked_at is None or self.unlock_at is None:
            return 0
        
        duration = (self.unlock_at - self.locked_at).total_seconds()
        return int(duration / 60)
    
    def manual_unlock(self, admin_id: uuid4) -> None:
        """
        手动解锁账户
        
        Args:
            admin_id: 执行解锁的管理员ID
        """
        self.is_auto_unlock = False
        self.unlocked_by = admin_id
        self.unlocked_at = datetime.now()
        self.unlock_at = datetime.now()  # 立即解锁
        self.updated_at = datetime.now()
    
    def auto_unlock(self) -> bool:
        """
        执行自动解锁检查
        
        Returns:
            bool: 如果已解锁返回True，否则返回False
        """
        if not self.is_locked:
            return False
        
        if self.unlock_at and datetime.now() >= self.unlock_at:
            self.updated_at = datetime.now()
            return True
        
        return False
    
    def extend_lock(self, additional_minutes: int = 15) -> None:
        """
        延长锁定时间
        
        Args:
            additional_minutes: 额外锁定分钟数
        """
        from datetime import timedelta
        
        if self.unlock_at:
            self.unlock_at += timedelta(minutes=additional_minutes)
        else:
            self.unlock_at = datetime.now() + timedelta(minutes=additional_minutes)
        
        self.locked_at = self.locked_at or datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """
        转换为字典
        
        Returns:
            dict: 锁定记录的字典表示
        """
        return {
            "id": self.id,
            "user_id": str(self.user_id),
            "lock_reason": self.lock_reason,
            "failed_attempts": self.failed_attempts,
            "locked_at": self.locked_at.isoformat() if self.locked_at else None,
            "unlock_at": self.unlock_at.isoformat() if self.unlock_at else None,
            "is_auto_unlock": self.is_auto_unlock,
            "unlocked_by": str(self.unlocked_by) if self.unlocked_by else None,
            "unlocked_at": self.unlocked_at.isoformat() if self.unlocked_at else None,
            "is_locked": self.is_locked,
            "remaining_seconds": self.get_remaining_lock_seconds(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def __repr__(self) -> str:
        """字符串表示"""
        status = "锁定中" if self.is_locked else "已解锁"
        remaining = self.get_remaining_lock_seconds()
        return f"<AccountLock(user_id={self.user_id}, status={status}, remaining={remaining}s)>"


# 锁定配置常量
class LockConfig:
    """锁定配置"""
    
    # 最大失败尝试次数
    MAX_ATTEMPTS: int = 5
    
    # 锁定时长（分钟）
    LOCK_DURATION_MINUTES: int = 15
    
    # 是否启用自动解锁
    AUTO_UNLOCK_ENABLED: bool = True
    
    # 锁定原因
    LOCK_REASON: str = "连续登录失败"
    
    # 管理员手动解锁原因
    ADMIN_UNLOCK_REASON: str = "管理员手动解锁"
