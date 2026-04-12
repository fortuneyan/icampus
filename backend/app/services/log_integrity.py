"""
日志完整性保护服务

提供日志签名和完整性验证，符合三级等保要求：
- 8.1.2.3 安全审计：日志保护
- 日志留存≥180天
- 防篡改机制

Author: AI
Date: 2026-04-11
"""

import hmac
import hashlib
import json
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from dataclasses import dataclass, field, asdict


class LogIntegrityConfig:
    """日志完整性配置"""
    
    # 签名算法
    SIGNATURE_ALGORITHM = "sha256"
    
    # 密钥轮换周期（天）
    KEY_ROTATION_DAYS = 30
    
    # 日志留存期（天）
    RETENTION_DAYS = 180
    
    # 哈希链块大小
    CHAIN_BLOCK_SIZE = 100
    
    # 签名格式版本
    SIGNATURE_VERSION = "1.0"


@dataclass
class LogEntry:
    """日志条目"""
    
    timestamp: str
    level: str
    module: str
    message: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    # 签名字段
    signature: Optional[str] = None
    previous_hash: Optional[str] = None
    sequence: int = 0
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
    
    @classmethod
    def from_dict(cls, data: dict) -> "LogEntry":
        """从字典创建"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class LogIntegrity:
    """
    日志完整性保护
    
    提供：
    - HMAC签名
    - 哈希链验证
    - 防篡改机制
    """
    
    def __init__(self, secret_key: str = None):
        """
        初始化
        
        Args:
            secret_key: 签名密钥
        """
        self.secret_key = secret_key or secrets.token_hex(32)
        self._last_hash: Optional[str] = None
        self._sequence: int = 0
    
    def sign_log(self, entry: LogEntry) -> str:
        """
        对日志条目进行签名
        
        Args:
            entry: 日志条目
            
        Returns:
            str: 签名
        """
        # 包含前一个哈希形成链
        entry.previous_hash = self._last_hash
        entry.sequence = self._sequence
        
        # 创建签名内容
        content = self._create_signing_content(entry)
        
        # 生成签名
        signature = hmac.new(
            self.secret_key.encode(),
            content.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # 更新状态
        self._last_hash = signature
        self._sequence += 1
        
        return signature
    
    def _create_signing_content(self, entry: LogEntry) -> str:
        """创建签名内容"""
        # 使用固定字段进行签名
        sign_data = {
            "timestamp": entry.timestamp,
            "level": entry.level,
            "module": entry.module,
            "message": entry.message,
            "user_id": entry.user_id,
            "ip_address": entry.ip_address,
            "request_id": entry.request_id,
            "previous_hash": entry.previous_hash,
            "sequence": entry.sequence,
        }
        
        # 排序后转为JSON
        return json.dumps(sign_data, ensure_ascii=False, sort_keys=True)
    
    def verify_log(self, entry: LogEntry) -> bool:
        """
        验证日志签名
        
        Args:
            entry: 日志条目
            
        Returns:
            bool: 签名是否有效
        """
        if entry.signature is None:
            return False
        
        # 重建签名内容
        content = self._create_signing_content(entry)
        
        # 计算期望签名
        expected = hmac.new(
            self.secret_key.encode(),
            content.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # 常量时间比较
        return hmac.compare_digest(entry.signature, expected)
    
    def create_hash_chain(self, entries: List[LogEntry]) -> str:
        """
        创建日志哈希链
        
        Args:
            entries: 日志条目列表
            
        Returns:
            str: 链的最终哈希
        """
        chain_hash = ""
        
        for entry in entries:
            entry.previous_hash = chain_hash
            signature = self.sign_log(entry)
            entry.signature = signature
            chain_hash = signature
        
        return chain_hash
    
    def verify_hash_chain(self, entries: List[LogEntry]) -> tuple:
        """
        验证哈希链完整性
        
        Args:
            entries: 日志条目列表
            
        Returns:
            tuple: (是否有效, 错误消息)
        """
        if not entries:
            return True, None
        
        # 验证第一个条目
        first = entries[0]
        if first.previous_hash != "":
            return False, f"First entry has non-empty previous_hash: {first.previous_hash}"
        
        previous_hash = ""
        
        for i, entry in enumerate(entries):
            # 验证previous_hash
            if entry.previous_hash != previous_hash:
                return False, f"Entry {i} has incorrect previous_hash"
            
            # 验证签名
            if not self.verify_log(entry):
                return False, f"Entry {i} has invalid signature"
            
            previous_hash = entry.signature
        
        return True, None
    
    def check_log_integrity(self, entry: LogEntry, expected_sequence: int) -> tuple:
        """
        检查日志完整性
        
        Args:
            entry: 日志条目
            expected_sequence: 期望的序列号
            
        Returns:
            tuple: (是否完整, 错误消息)
        """
        # 检查序列号
        if entry.sequence != expected_sequence:
            return False, f"Sequence mismatch: expected {expected_sequence}, got {entry.sequence}"
        
        # 检查时间戳格式
        try:
            datetime.fromisoformat(entry.timestamp)
        except ValueError:
            return False, f"Invalid timestamp format: {entry.timestamp}"
        
        # 验证签名
        if not self.verify_log(entry):
            return False, "Signature verification failed"
        
        return True, None


class LogIntegrityService:
    """
    日志完整性服务
    
    提供日志保护和管理功能。
    """
    
    def __init__(self, secret_key: str = None):
        """
        初始化
        
        Args:
            secret_key: 签名密钥
        """
        self.integrity = LogIntegrity(secret_key)
        self._log_buffer: List[LogEntry] = []
        self._buffer_size = 100
    
    def create_signed_entry(
        self,
        level: str,
        module: str,
        message: str,
        user_id: str = None,
        ip_address: str = None,
        request_id: str = None,
        metadata: dict = None,
    ) -> LogEntry:
        """
        创建签名的日志条目
        
        Args:
            level: 日志级别
            module: 模块名
            message: 日志消息
            user_id: 用户ID
            ip_address: IP地址
            request_id: 请求ID
            metadata: 元数据
            
        Returns:
            LogEntry: 签名的日志条目
        """
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            module=module,
            message=message,
            user_id=user_id,
            ip_address=ip_address,
            request_id=request_id,
            metadata=metadata or {},
        )
        
        # 签名
        signature = self.integrity.sign_log(entry)
        entry.signature = signature
        
        # 缓冲
        self._log_buffer.append(entry)
        
        # 定期刷新
        if len(self._log_buffer) >= self._buffer_size:
            self.flush()
        
        return entry
    
    def flush(self) -> List[LogEntry]:
        """
        刷新缓冲区
        
        Returns:
            List[LogEntry]: 刷新的日志条目
        """
        entries = self._log_buffer.copy()
        self._log_buffer.clear()
        return entries
    
    def verify_entries(self, entries: List[LogEntry]) -> Dict:
        """
        验证日志条目列表
        
        Args:
            entries: 日志条目列表
            
        Returns:
            Dict: 验证结果
        """
        if not entries:
            return {"valid": True, "total": 0, "invalid": 0, "errors": []}
        
        # 验证哈希链
        chain_valid, chain_error = self.integrity.verify_hash_chain(entries)
        
        result = {
            "valid": chain_valid,
            "total": len(entries),
            "invalid": 0 if chain_valid else len(entries),
            "errors": [chain_error] if chain_error else [],
        }
        
        return result
    
    def get_retention_days(self) -> int:
        """
        获取日志留存天数
        
        Returns:
            int: 留存天数
        """
        return LogIntegrityConfig.RETENTION_DAYS
    
    def is_within_retention(self, timestamp: str) -> bool:
        """
        检查日志是否在留存期内
        
        Args:
            timestamp: ISO格式时间戳
            
        Returns:
            bool: 是否在留存期内
        """
        try:
            dt = datetime.fromisoformat(timestamp)
            age = datetime.now() - dt
            return age.days < LogIntegrityConfig.RETENTION_DAYS
        except ValueError:
            return False


# 全局服务实例
_log_integrity_service: Optional[LogIntegrityService] = None


def get_log_integrity_service() -> LogIntegrityService:
    """
    获取全局日志完整性服务
    
    Returns:
        LogIntegrityService: 服务实例
    """
    global _log_integrity_service
    if _log_integrity_service is None:
        _log_integrity_service = LogIntegrityService()
    return _log_integrity_service
