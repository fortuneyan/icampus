"""
MFA数据模型

存储MFA配置信息，符合三级等保要求：
- 8.1.2.1 身份鉴别：多因素认证

Author: AI
Date: 2026-04-11
"""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from dataclasses import dataclass, field


@dataclass
class MFASecret:
    """
    MFA秘钥存储
    
    Attributes:
        id: 记录ID
        user_id: 用户ID
        encrypted_secret: 加密的TOTP秘钥
        backup_codes_hash: 备用码哈希列表
        is_enabled: 是否启用
        is_verified: 是否已验证
        created_at: 创建时间
        verified_at: 验证时间
        last_used_at: 最后使用时间
    """
    
    id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    encrypted_secret: str = ""
    backup_codes_hash: List[str] = field(default_factory=list)
    is_enabled: bool = False
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    verified_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    
    def enable(self) -> None:
        """启用MFA"""
        self.is_enabled = True
        self.verified_at = datetime.now()
    
    def disable(self) -> None:
        """禁用MFA"""
        self.is_enabled = False
    
    def mark_used(self) -> None:
        """标记已使用"""
        self.last_used_at = datetime.now()
    
    def add_backup_code(self, code_hash: str) -> None:
        """添加备用码"""
        if code_hash not in self.backup_codes_hash:
            self.backup_codes_hash.append(code_hash)
    
    def remove_backup_code(self, code_hash: str) -> bool:
        """移除备用码"""
        if code_hash in self.backup_codes_hash:
            self.backup_codes_hash.remove(code_hash)
            return True
        return False
    
    def get_backup_codes_remaining(self) -> int:
        """获取剩余备用码数量"""
        return len(self.backup_codes_hash)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "is_enabled": self.is_enabled,
            "is_verified": self.is_verified,
            "backup_codes_remaining": self.get_backup_codes_remaining(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }


@dataclass
class MFAEnableResult:
    """MFA启用结果"""
    
    secret: str  # Base32编码的秘钥
    qr_code_url: str  # 二维码URL
    manual_entry_key: str  # 手动输入密钥
    backup_codes: List[str]  # 备用码


@dataclass  
class MFAVerifyResult:
    """MFA验证结果"""
    
    success: bool
    message: str
    remaining_attempts: int = 0
    backup_codes_remaining: int = 0
