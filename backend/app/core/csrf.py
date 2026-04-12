"""
CSRF防护核心

提供CSRF Token生成和验证功能，符合三级等保要求：
- 8.1.2.2 访问控制：防止CSRF攻击

Author: AI
Date: 2026-04-11
"""

import secrets
import hmac
import hashlib
from typing import Optional


class CSRFConfig:
    """CSRF配置"""
    
    # Token配置
    TOKEN_LENGTH = 32  # Token字节长度
    SECRET_LENGTH = 32  # 密钥字节长度
    
    # Cookie/Header配置
    TOKEN_NAME = "csrftoken"  # Cookie名称
    HEADER_NAME = "X-CSRF-Token"  # 请求头名称
    
    # Cookie配置
    COOKIE_SECURE = True  # HTTPS only
    COOKIE_HTTPONLY = False  # 前端需要读取
    COOKIE_SAMESITE = "lax"  # CSRF protection
    
    # Token有效期（秒）
    TOKEN_EXPIRY = 3600  # 1小时
    
    # 豁免的HTTP方法
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


class CSRFToken:
    """
    CSRF Token管理器
    
    提供Token的生成、验证、存储等功能。
    """
    
    @staticmethod
    def generate(secret: str = None) -> str:
        """
        生成CSRF Token
        
        Args:
            secret: 可选的密钥
            
        Returns:
            str: 64字符的十六进制Token
        """
        if secret:
            # 使用HMAC生成带密钥的Token
            random_bytes = secrets.token_bytes(CSRFConfig.TOKEN_LENGTH)
            token = hmac.new(
                secret.encode(),
                random_bytes,
                hashlib.sha256
            ).hexdigest()
        else:
            # 使用secrets生成安全的随机Token
            token = secrets.token_hex(CSRFConfig.TOKEN_LENGTH)
        
        return token
    
    @staticmethod
    def generate_secret() -> str:
        """
        生成CSRF密钥
        
        Returns:
            str: 安全的随机密钥
        """
        return secrets.token_hex(CSRFConfig.SECRET_LENGTH)
    
    @staticmethod
    def verify(token: str, stored_token: str, secret: str = None) -> bool:
        """
        验证Token
        
        Args:
            token: 请求中的Token
            stored_token: 存储的Token
            secret: 可选的密钥
            
        Returns:
            bool: Token是否有效
        """
        if not token or not stored_token:
            return False
        
        if len(token) != len(stored_token):
            return False
        
        # 使用常量时间比较防止时序攻击
        return CSRFUtils.constant_time_compare(token, stored_token)
    
    @staticmethod
    def create_signed_token(user_id: str, secret: str) -> str:
        """
        创建签名Token
        
        包含用户标识和签名，防止Token被用于其他用户。
        
        Args:
            user_id: 用户ID
            secret: 密钥
            
        Returns:
            str: 签名的Token
        """
        timestamp = str(int(__import__('time').time()))
        random_data = secrets.token_hex(16)
        
        message = f"{user_id}:{timestamp}:{random_data}"
        
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{message}:{signature}"
    
    @staticmethod
    def verify_signed_token(token: str, user_id: str, secret: str) -> bool:
        """
        验证签名Token
        
        Args:
            token: 签名的Token
            user_id: 用户ID
            secret: 密钥
            
        Returns:
            bool: Token是否有效且属于该用户
        """
        try:
            parts = token.split(":")
            if len(parts) != 4:
                return False
            
            stored_user_id, timestamp, random_data, signature = parts
            
            # 验证用户ID
            if stored_user_id != user_id:
                return False
            
            # 验证时间戳
            import time
            token_time = int(timestamp)
            current_time = int(time.time())
            
            if current_time - token_time > CSRFConfig.TOKEN_EXPIRY:
                return False
            
            # 验证签名
            message = f"{user_id}:{timestamp}:{random_data}"
            expected_signature = hmac.new(
                secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return CSRFUtils.constant_time_compare(signature, expected_signature)
            
        except (ValueError, TypeError):
            return False


class CSRFUtils:
    """CSRF工具函数"""
    
    @staticmethod
    def constant_time_compare(val1: str, val2: str) -> bool:
        """
        常量时间字符串比较
        
        防止时序攻击。
        
        Args:
            val1: 第一个字符串
            val2: 第二个字符串
            
        Returns:
            bool: 字符串是否相等
        """
        return hmac.compare_digest(val1, val2)
    
    @staticmethod
    def mask_token(token: str) -> str:
        """
        遮蔽Token
        
        用于日志记录等场景，保护Token安全。
        
        Args:
            token: 原始Token
            
        Returns:
            str: 遮蔽后的Token
        """
        if len(token) <= 8:
            return "*" * len(token)
        
        return token[:4] + "*" * (len(token) - 8) + token[-4:]
    
    @staticmethod
    def generate_random_bytes(length: int) -> bytes:
        """
        生成安全的随机字节
        
        Args:
            length: 字节长度
            
        Returns:
            bytes: 随机字节
        """
        return secrets.token_bytes(length)
    
    @staticmethod
    def hex_encode(data: bytes) -> str:
        """
        十六进制编码
        
        Args:
            data: 字节数据
            
        Returns:
            str: 十六进制字符串
        """
        return data.hex()
    
    @staticmethod
    def hex_decode(hex_string: str) -> bytes:
        """
        十六进制解码
        
        Args:
            hex_string: 十六进制字符串
            
        Returns:
            bytes: 字节数据
        """
        return bytes.fromhex(hex_string)
    
    @staticmethod
    def is_safe_method(method: str) -> bool:
        """
        检查是否为安全HTTP方法
        
        安全方法不需要CSRF验证。
        
        Args:
            method: HTTP方法
            
        Returns:
            bool: 是否为安全方法
        """
        return method.upper() in CSRFConfig.SAFE_METHODS
