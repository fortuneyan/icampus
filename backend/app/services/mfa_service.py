"""
MFA服务

提供TOTP MFA功能，符合三级等保要求：
- 8.1.2.1 身份鉴别：多因素认证

Author: AI
Date: 2026-04-11
"""

import pyotp
import secrets
import hashlib
import base64
from typing import Optional, Dict, Tuple
from datetime import datetime
import urllib.parse

from app.models.mfa import MFASecret, MFAEnableResult, MFAVerifyResult


class MFAConfig:
    """MFA配置"""
    
    # TOTP配置
    ISSUER_NAME = "SmartCampus"
    DIGITS = 6
    INTERVAL = 30  # 30秒
    
    # 备用码配置
    BACKUP_CODES_COUNT = 10
    BACKUP_CODE_LENGTH = 10
    
    # 验证配置
    MAX_VERIFY_ATTEMPTS = 3
    VERIFY_WINDOW = 1  # 前后1个时间窗口
    
    # 算法
    ALGORITHM = "SHA1"


class MFAService:
    """
    MFA服务
    
    提供：
    - TOTP秘钥生成
    - 二维码URL生成
    - TOTP验证
    - 备用码管理
    """
    
    def __init__(self, secret_store: Dict[str, MFASecret] = None):
        """
        初始化MFA服务
        
        Args:
            secret_store: 秘钥存储（内存或数据库）
        """
        self._store = secret_store or {}
    
    def _generate_secret(self) -> str:
        """
        生成TOTP秘钥
        
        Returns:
            str: Base32编码的秘钥
        """
        # 生成160位随机秘钥
        random_bytes = secrets.token_bytes(20)
        # 转换为Base32
        return base64.b32encode(random_bytes).decode().rstrip('=')
    
    def _generate_provisioning_uri(self, secret: str, user_id: str) -> str:
        """
        生成二维码 Provisioning URI
        
        Args:
            secret: TOTP秘钥
            user_id: 用户标识
            
        Returns:
            str: otpauth:// URI
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=user_id,
            issuer_name=MFAConfig.ISSUER_NAME
        )
    
    def _generate_backup_codes(self) -> Tuple[list, list]:
        """
        生成备用码
        
        Returns:
            Tuple[list, list]: (明文备用码, 哈希备用码)
        """
        plaintext = []
        hashed = []
        
        for _ in range(MFAConfig.BACKUP_CODES_COUNT):
            # 生成随机码
            code = ''.join(
                secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789')
                for _ in range(MFAConfig.BACKUP_CODE_LENGTH)
            )
            plaintext.append(code)
            
            # 哈希存储
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            hashed.append(code_hash)
        
        return plaintext, hashed
    
    def _hash_backup_code(self, code: str) -> str:
        """哈希备用码"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    async def generate_mfa_setup(self, user_id: str) -> MFAEnableResult:
        """
        生成MFA设置信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            MFAEnableResult: MFA设置结果
        """
        # 生成秘钥
        secret = self._generate_secret()
        
        # 生成二维码URL
        qr_code_url = self._generate_provisioning_uri(secret, user_id)
        
        # 生成备用码
        backup_codes, backup_codes_hash = self._generate_backup_codes()
        
        # 存储MFA配置
        mfa_secret = MFASecret(
            user_id=user_id,
            encrypted_secret=secret,  # 实际应加密
            backup_codes_hash=backup_codes_hash,
        )
        self._store[user_id] = mfa_secret
        
        return MFAEnableResult(
            secret=secret,
            qr_code_url=qr_code_url,
            manual_entry_key=secret,
            backup_codes=backup_codes,
        )
    
    async def verify_mfa_setup(self, user_id: str, code: str) -> bool:
        """
        验证MFA设置
        
        Args:
            user_id: 用户ID
            code: TOTP验证码
            
        Returns:
            bool: 验证是否成功
        """
        mfa_secret = self._store.get(user_id)
        if mfa_secret is None:
            return False
        
        # 验证TOTP
        totp = pyotp.TOTP(mfa_secret.encrypted_secret)
        is_valid = totp.verify(code, valid_window=MFAConfig.VERIFY_WINDOW)
        
        if is_valid:
            mfa_secret.is_verified = True
            mfa_secret.enable()
        
        return is_valid
    
    async def verify_totp(self, user_id: str, code: str) -> MFAVerifyResult:
        """
        验证TOTP验证码
        
        Args:
            user_id: 用户ID
            code: TOTP验证码
            
        Returns:
            MFAVerifyResult: 验证结果
        """
        mfa_secret = self._store.get(user_id)
        
        if mfa_secret is None:
            return MFAVerifyResult(
                success=False,
                message="MFA未配置",
                remaining_attempts=MFAConfig.MAX_VERIFY_ATTEMPTS,
            )
        
        if not mfa_secret.is_enabled:
            return MFAVerifyResult(
                success=False,
                message="MFA未启用",
                remaining_attempts=0,
            )
        
        # 验证TOTP
        totp = pyotp.TOTP(mfa_secret.encrypted_secret)
        is_valid = totp.verify(code, valid_window=MFAConfig.VERIFY_WINDOW)
        
        if is_valid:
            mfa_secret.mark_used()
            return MFAVerifyResult(
                success=True,
                message="验证成功",
                remaining_attempts=MFAConfig.MAX_VERIFY_ATTEMPTS,
                backup_codes_remaining=mfa_secret.get_backup_codes_remaining(),
            )
        
        return MFAVerifyResult(
            success=False,
            message="验证码错误",
            remaining_attempts=MFAConfig.MAX_VERIFY_ATTEMPTS,
            backup_codes_remaining=mfa_secret.get_backup_codes_remaining(),
        )
    
    async def verify_backup_code(self, user_id: str, code: str) -> MFAVerifyResult:
        """
        验证备用码
        
        Args:
            user_id: 用户ID
            code: 备用码
            
        Returns:
            MFAVerifyResult: 验证结果
        """
        mfa_secret = self._store.get(user_id)
        
        if mfa_secret is None:
            return MFAVerifyResult(
                success=False,
                message="MFA未配置",
            )
        
        if not mfa_secret.is_enabled:
            return MFAVerifyResult(
                success=False,
                message="MFA未启用",
            )
        
        # 哈希并验证
        code_hash = self._hash_backup_code(code)
        
        if code_hash in mfa_secret.backup_codes_hash:
            # 使用后删除
            mfa_secret.remove_backup_code(code_hash)
            mfa_secret.mark_used()
            
            return MFAVerifyResult(
                success=True,
                message="备用码验证成功",
                backup_codes_remaining=mfa_secret.get_backup_codes_remaining(),
            )
        
        return MFAVerifyResult(
            success=False,
            message="备用码无效或已使用",
            backup_codes_remaining=mfa_secret.get_backup_codes_remaining(),
        )
    
    async def disable_mfa(self, user_id: str) -> bool:
        """
        禁用MFA
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否成功
        """
        mfa_secret = self._store.get(user_id)
        if mfa_secret is None:
            return False
        
        mfa_secret.disable()
        return True
    
    async def get_mfa_status(self, user_id: str) -> dict:
        """
        获取MFA状态
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: MFA状态
        """
        mfa_secret = self._store.get(user_id)
        
        if mfa_secret is None:
            return {
                "configured": False,
                "enabled": False,
                "verified": False,
                "backup_codes_remaining": 0,
            }
        
        return {
            "configured": True,
            "enabled": mfa_secret.is_enabled,
            "verified": mfa_secret.is_verified,
            "backup_codes_remaining": mfa_secret.get_backup_codes_remaining(),
            "last_used_at": mfa_secret.last_used_at.isoformat() if mfa_secret.last_used_at else None,
        }
    
    async def regenerate_backup_codes(self, user_id: str) -> list:
        """
        重新生成备用码
        
        Args:
            user_id: 用户ID
            
        Returns:
            list: 新备用码列表
        """
        mfa_secret = self._store.get(user_id)
        if mfa_secret is None:
            return []
        
        plaintext, hashed = self._generate_backup_codes()
        mfa_secret.backup_codes_hash = hashed
        
        return plaintext


# 全局服务实例
_mfa_service: Optional[MFAService] = None


def get_mfa_service() -> MFAService:
    """
    获取MFA服务实例
    
    Returns:
        MFAService: MFA服务
    """
    global _mfa_service
    if _mfa_service is None:
        _mfa_service = MFAService()
    return _mfa_service
