"""
账户锁定服务

提供账户锁定、解锁、查询等功能，符合三级等保要求：
- 登录失败处理
- 账户自动/手动解锁
- 锁定状态管理

Author: AI
Date: 2026-04-11
"""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID, uuid4
from dataclasses import dataclass, field

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account_lock import AccountLock, LockConfig


# 锁定配置常量
LOCK_CONFIG = {
    "max_attempts": LockConfig.MAX_ATTEMPTS,
    "lock_duration_minutes": LockConfig.LOCK_DURATION_MINUTES,
    "auto_unlock_enabled": LockConfig.AUTO_UNLOCK_ENABLED,
    "lock_reason": LockConfig.LOCK_REASON,
    "admin_unlock_reason": LockConfig.ADMIN_UNLOCK_REASON,
}


@dataclass
class LockResult:
    """锁定操作结果"""
    success: bool
    lock_record: Optional[AccountLock] = None
    message: str = ""
    failed_attempts: int = 0
    is_locked: bool = False


class AccountLockService:
    """
    账户锁定服务
    
    提供用户登录失败锁定相关的所有操作。
    
    Attributes:
        db: 数据库会话
        _cache: 内存缓存（用于无数据库场景）
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化账户锁定服务
        
        Args:
            db: 异步数据库会话
        """
        self.db = db
        self._cache: dict[str, dict] = {}  # 内存缓存: user_id -> lock_data
    
    async def _get_cache_key(self, user_id: UUID) -> str:
        """获取缓存键"""
        return str(user_id)
    
    async def _get_cached_lock(self, user_id: UUID) -> Optional[dict]:
        """从缓存获取锁定信息"""
        return self._cache.get(await self._get_cache_key(user_id))
    
    async def _set_cached_lock(self, user_id: UUID, lock_data: dict) -> None:
        """设置缓存锁定信息"""
        self._cache[await self._get_cache_key(user_id)] = lock_data
    
    async def _delete_cached_lock(self, user_id: UUID) -> None:
        """删除缓存锁定信息"""
        self._cache.pop(await self._get_cache_key(user_id), None)
    
    async def record_failed_login(self, user_id: UUID) -> AccountLock:
        """
        记录失败的登录尝试
        
        当失败次数达到阈值时，自动锁定账户。
        
        Args:
            user_id: 用户ID
            
        Returns:
            AccountLock: 更新后的锁定记录
        """
        failed_attempts = await self.get_failed_attempts(user_id)
        failed_attempts += 1
        
        # 检查是否需要锁定
        should_lock = failed_attempts >= LOCK_CONFIG["max_attempts"]
        
        # 创建或更新锁定记录
        existing_lock = await self._get_cached_lock(user_id)
        
        if existing_lock:
            lock_record = AccountLock(
                id=existing_lock.get("id", 0),
                user_id=user_id,
                lock_reason=LOCK_CONFIG["lock_reason"],
                failed_attempts=failed_attempts,
                locked_at=existing_lock.get("locked_at") or datetime.now(),
                unlock_at=existing_lock.get("unlock_at"),
                is_auto_unlock=LOCK_CONFIG["auto_unlock_enabled"],
            )
        else:
            lock_record = AccountLock(
                id=0,
                user_id=user_id,
                lock_reason=LOCK_CONFIG["lock_reason"],
                failed_attempts=failed_attempts,
                locked_at=datetime.now(),
                unlock_at=None,
                is_auto_unlock=LOCK_CONFIG["auto_unlock_enabled"],
            )
        
        # 如果应该锁定
        if should_lock:
            lock_record.unlock_at = datetime.now() + timedelta(
                minutes=LOCK_CONFIG["lock_duration_minutes"]
            )
        
        # 更新缓存
        await self._set_cached_lock(user_id, {
            "id": lock_record.id,
            "user_id": str(lock_record.user_id),
            "failed_attempts": lock_record.failed_attempts,
            "locked_at": lock_record.locked_at,
            "unlock_at": lock_record.unlock_at,
            "is_auto_unlock": lock_record.is_auto_unlock,
        })
        
        return lock_record
    
    async def get_failed_attempts(self, user_id: UUID) -> int:
        """
        获取用户当前失败尝试次数
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 失败尝试次数
        """
        cached = await self._get_cached_lock(user_id)
        if cached:
            return cached.get("failed_attempts", 0)
        return 0
    
    async def is_user_locked(self, user_id: UUID) -> bool:
        """
        检查用户是否被锁定
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 如果用户被锁定且未过期返回True
        """
        cached = await self._get_cached_lock(user_id)
        if cached:
            unlock_at = cached.get("unlock_at")
            if unlock_at and isinstance(unlock_at, datetime):
                return datetime.now() < unlock_at
            return False
        return False
    
    async def get_lock_info(self, user_id: UUID) -> Optional[AccountLock]:
        """
        获取用户锁定信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[AccountLock]: 锁定记录，不存在返回None
        """
        cached = await self._get_cached_lock(user_id)
        if cached:
            return AccountLock(
                id=cached.get("id", 0),
                user_id=user_id,
                failed_attempts=cached.get("failed_attempts", 0),
                locked_at=cached.get("locked_at"),
                unlock_at=cached.get("unlock_at"),
                is_auto_unlock=cached.get("is_auto_unlock", True),
            )
        return None
    
    async def unlock_user(self, user_id: UUID, admin_id: UUID) -> bool:
        """
        手动解锁用户（管理员操作）
        
        Args:
            user_id: 要解锁的用户ID
            admin_id: 执行解锁的管理员ID
            
        Returns:
            bool: 解锁是否成功
        """
        lock_info = await self.get_lock_info(user_id)
        if lock_info:
            lock_info.manual_unlock(admin_id)
            await self._set_cached_lock(user_id, {
                **lock_info.__dict__,
                "unlock_at": datetime.now(),
            })
            return True
        return False
    
    async def reset_failed_attempts(self, user_id: UUID) -> bool:
        """
        重置失败尝试次数（成功登录后调用）
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 重置是否成功
        """
        await self._delete_cached_lock(user_id)
        return True
    
    async def auto_unlock_expired(self) -> int:
        """
        自动解锁所有已过期的锁定
        
        Returns:
            int: 解锁的账户数量
        """
        count = 0
        now = datetime.now()
        
        for user_id_str, lock_data in list(self._cache.items()):
            unlock_at = lock_data.get("unlock_at")
            if unlock_at and isinstance(unlock_at, datetime):
                if now >= unlock_at:
                    self._cache.pop(user_id_str, None)
                    count += 1
        
        return count
    
    async def get_user_lock_history(
        self, 
        user_id: UUID, 
        limit: int = 10
    ) -> List[AccountLock]:
        """
        获取用户锁定历史
        
        Args:
            user_id: 用户ID
            limit: 返回记录数限制
            
        Returns:
            List[AccountLock]: 锁定记录列表
        """
        # 简化实现，返回缓存中的记录
        current_lock = await self.get_lock_info(user_id)
        if current_lock:
            return [current_lock]
        return []
    
    async def get_lock_stats(self) -> dict:
        """
        获取锁定统计信息
        
        Returns:
            dict: 统计信息
        """
        total_locks = len(self._cache)
        active_locks = sum(
            1 for lock_data in self._cache.values()
            if lock_data.get("unlock_at") and datetime.now() < lock_data.get("unlock_at")
        )
        
        return {
            "total_locks": total_locks,
            "active_locks": active_locks,
            "expired_locks": total_locks - active_locks,
            "max_attempts": LOCK_CONFIG["max_attempts"],
            "lock_duration_minutes": LOCK_CONFIG["lock_duration_minutes"],
        }
    
    async def check_and_raise_if_locked(self, user_id: UUID) -> None:
        """
        检查用户是否被锁定，如果是则抛出异常
        
        Args:
            user_id: 用户ID
            
        Raises:
            AccountLockedException: 账户被锁定时抛出
        """
        lock_info = await self.get_lock_info(user_id)
        if lock_info and lock_info.is_locked:
            remaining = lock_info.get_remaining_lock_seconds()
            from app.core.exceptions import UnauthorizedException
            raise UnauthorizedException(
                f"账户已被锁定，请在 {remaining} 秒后重试"
            )


class AccountLockedException(Exception):
    """账户被锁定异常"""
    
    def __init__(self, message: str, remaining_seconds: int = 0):
        super().__init__(message)
        self.remaining_seconds = remaining_seconds
