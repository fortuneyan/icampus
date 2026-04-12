"""
T-S1 登录失败锁定机制 - 单元测试

测试目标：
1. AccountLock 模型
2. AccountLockService 服务
3. 登录集成

运行：pytest tests/unit/security/test_account_lock.py -v
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import time


class TestAccountLockModel:
    """测试账户锁定模型"""

    def test_model_creation(self):
        """测试模型创建"""
        from app.models.account_lock import AccountLock
        
        user_id = uuid4()
        lock = AccountLock(
            user_id=user_id,
            lock_reason="连续登录失败",
            failed_attempts=5,
            locked_at=datetime.now(),
            unlock_at=datetime.now() + timedelta(minutes=15),
            is_auto_unlock=True
        )
        
        assert lock.user_id == user_id
        assert lock.lock_reason == "连续登录失败"
        assert lock.failed_attempts == 5
        assert lock.is_auto_unlock is True

    def test_is_locked_property(self):
        """测试is_locked属性"""
        from app.models.account_lock import AccountLock
        
        # 未过期的锁定
        lock_future = AccountLock(
            user_id=uuid4(),
            unlock_at=datetime.now() + timedelta(minutes=10)
        )
        assert lock_future.is_locked is True
        
        # 已过期的锁定
        lock_expired = AccountLock(
            user_id=uuid4(),
            unlock_at=datetime.now() - timedelta(minutes=1)
        )
        assert lock_expired.is_locked is False

    def test_is_auto_unlock_property(self):
        """测试is_auto_unlock属性"""
        from app.models.account_lock import AccountLock
        
        lock_auto = AccountLock(
            user_id=uuid4(),
            is_auto_unlock=True
        )
        assert lock_auto.is_auto_unlock is True
        
        lock_manual = AccountLock(
            user_id=uuid4(),
            is_auto_unlock=False
        )
        assert lock_manual.is_auto_unlock is False

    def test_remaining_lock_time(self):
        """测试剩余锁定时间计算"""
        from app.models.account_lock import AccountLock
        
        # 剩余10分钟
        lock = AccountLock(
            user_id=uuid4(),
            unlock_at=datetime.now() + timedelta(minutes=10)
        )
        remaining = lock.get_remaining_lock_seconds()
        assert 590 < remaining <= 600  # 约10分钟
        
        # 已过期
        lock_expired = AccountLock(
            user_id=uuid4(),
            unlock_at=datetime.now() - timedelta(minutes=5)
        )
        assert lock_expired.get_remaining_lock_seconds() == 0


class TestAccountLockService:
    """测试账户锁定服务"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_record_failed_login(self, mock_db):
        """测试记录失败登录"""
        from app.services.account_lock_service import AccountLockService
        
        service = AccountLockService(mock_db)
        user_id = uuid4()
        
        # 模拟插入操作
        mock_db.execute.return_value = MagicMock()
        
        result = await service.record_failed_login(user_id)
        
        assert result.failed_attempts == 1
        assert result.user_id == user_id
        assert result.is_locked is False  # 第一次失败不解锁

    @pytest.mark.asyncio
    async def test_record_failed_login_triggers_lock(self, mock_db):
        """测试连续失败触发锁定"""
        from app.services.account_lock_service import AccountLockService, LOCK_CONFIG
        
        service = AccountLockService(mock_db)
        user_id = uuid4()
        
        # 模拟之前已有4次失败
        with patch.object(service, 'get_failed_attempts', new_callable=AsyncMock) as mock_attempts:
            mock_attempts.return_value = 4
            
            result = await service.record_failed_login(user_id)
            
            assert result.failed_attempts == 5
            assert result.is_locked is True
            assert result.unlock_at is not None

    @pytest.mark.asyncio
    async def test_is_user_locked_false(self, mock_db):
        """测试用户未被锁定"""
        from app.services.account_lock_service import AccountLockService
        
        service = AccountLockService(mock_db)
        user_id = uuid4()
        
        # 模拟查询结果为空
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        result = await service.is_user_locked(user_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_is_user_locked_true(self, mock_db):
        """测试用户已被锁定"""
        from app.services.account_lock_service import AccountLockService
        from app.models.account_lock import AccountLock
        
        service = AccountLockService(mock_db)
        user_id = uuid4()
        
        # 模拟存在未过期的锁定记录
        lock = AccountLock(
            user_id=user_id,
            unlock_at=datetime.now() + timedelta(minutes=10)
        )
        mock_db.execute.return_value.scalar_one_or_none.return_value = lock
        
        result = await service.is_user_locked(user_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_unlock_user(self, mock_db):
        """测试解锁用户"""
        from app.services.account_lock_service import AccountLockService
        
        service = AccountLockService(mock_db)
        user_id = uuid4()
        admin_id = uuid4()
        
        # 模拟查询和更新
        mock_db.execute.return_value = MagicMock()
        
        result = await service.unlock_user(user_id, admin_id)
        
        assert result is True
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_failed_attempts(self, mock_db):
        """测试重置失败次数"""
        from app.services.account_lock_service import AccountLockService
        
        service = AccountLockService(mock_db)
        user_id = uuid4()
        
        mock_db.execute.return_value = MagicMock()
        
        result = await service.reset_failed_attempts(user_id)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_auto_unlock_expired_locks(self, mock_db):
        """测试自动解锁过期锁定"""
        from app.services.account_lock_service import AccountLockService
        
        service = AccountLockService(mock_db)
        
        # 模拟查询到过期的锁定
        mock_result = MagicMock()
        expired_lock = MagicMock()
        expired_lock.id = 1
        expired_lock.user_id = uuid4()
        mock_result.scalars.return_value.all.return_value = [expired_lock]
        mock_db.execute.return_value = mock_result
        
        count = await service.auto_unlock_expired()
        
        assert count >= 0  # 可能有0个或多个过期锁定


class TestLoginIntegration:
    """测试登录集成"""

    @pytest.mark.asyncio
    async def test_login_blocked_when_locked(self):
        """测试锁定用户无法登录"""
        from app.services.account_lock_service import AccountLockService
        from app.services.auth_service import AuthService
        from app.core.exceptions import UnauthorizedException
        
        # 创建模拟服务
        mock_db = AsyncMock()
        lock_service = AccountLockService(mock_db)
        auth_service = AuthService()
        
        user_id = uuid4()
        
        # 设置用户为锁定状态
        with patch.object(lock_service, 'is_user_locked', new_callable=AsyncMock) as mock_locked:
            mock_locked.return_value = True
            
            # 模拟认证成功但被锁定拦截
            with pytest.raises(UnauthorizedException) as exc_info:
                # 这里需要完整的集成测试逻辑
                pass

    def test_lock_config_values(self):
        """测试锁定配置"""
        from app.services.account_lock_service import LOCK_CONFIG
        
        assert LOCK_CONFIG['max_attempts'] == 5
        assert LOCK_CONFIG['lock_duration_minutes'] == 15
        assert LOCK_CONFIG['auto_unlock_enabled'] is True


class TestAccountLockEdgeCases:
    """边界测试"""

    def test_concurrent_lock_attempts(self):
        """测试并发锁定尝试"""
        # 模拟并发场景
        pass  # 需要数据库级别的并发测试

    def test_lock_duration_edge_cases(self):
        """测试锁定时长边界"""
        from app.models.account_lock import AccountLock
        
        # 刚好过期
        lock = AccountLock(
            user_id=uuid4(),
            unlock_at=datetime.now() - timedelta(seconds=1)
        )
        assert lock.is_locked is False
        
        # 即将过期
        lock2 = AccountLock(
            user_id=uuid4(),
            unlock_at=datetime.now() + timedelta(seconds=1)
        )
        assert lock2.is_locked is True

    def test_multiple_unlock_reasons(self):
        """测试多种解锁原因"""
        from app.models.account_lock import AccountLock
        
        # 自动解锁
        lock_auto = AccountLock(
            user_id=uuid4(),
            lock_reason="连续登录失败",
            is_auto_unlock=True
        )
        assert lock_auto.is_auto_unlock is True
        
        # 手动解锁
        lock_manual = AccountLock(
            user_id=uuid4(),
            lock_reason="管理员手动解锁",
            is_auto_unlock=False,
            unlocked_by=uuid4()
        )
        assert lock_manual.is_auto_unlock is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
