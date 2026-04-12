"""
密码复杂度验证Schema

提供密码复杂度验证功能，符合三级等保要求：
- 8.1.2.1 身份鉴别：密码复杂性要求

密码规则：
- 最少8个字符
- 至少1个大写字母
- 至少1个小写字母
- 至少1个数字
- 至少1个特殊字符 (!@#$%^&*)

Author: AI
Date: 2026-04-11
"""

import re
from enum import Enum
from typing import List, Tuple


class PasswordValidation:
    """
    密码复杂度验证器
    
    类属性:
        MIN_LENGTH: 最小长度
        MIN_UPPERCASE: 大写字母最小数量
        MIN_LOWERCASE: 小写字母最小数量
        MIN_DIGITS: 数字最小数量
        MIN_SPECIAL: 特殊字符最小数量
        SPECIAL_CHARS: 特殊字符列表
    """
    
    # 最小长度要求
    MIN_LENGTH = 8
    
    # 各类型字符最小数量
    MIN_UPPERCASE = 1
    MIN_LOWERCASE = 1
    MIN_DIGITS = 1
    MIN_SPECIAL = 1
    
    # 特殊字符列表
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # 正则表达式
    UPPERCASE_PATTERN = re.compile(r'[A-Z]')
    LOWERCASE_PATTERN = re.compile(r'[a-z]')
    DIGIT_PATTERN = re.compile(r'[0-9]')
    SPECIAL_PATTERN = re.compile(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]')
    
    @classmethod
    def validate(cls, password: str) -> Tuple[bool, List[str]]:
        """
        验证密码复杂度
        
        Args:
            password: 待验证的密码
            
        Returns:
            Tuple[bool, List[str]]: (是否通过, 错误列表)
        """
        errors = []
        
        # 检查长度
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"密码长度至少{cls.MIN_LENGTH}个字符")
        
        # 检查大写字母
        if not cls.UPPERCASE_PATTERN.search(password):
            errors.append("密码必须包含至少1个大写字母")
        
        # 检查小写字母
        if not cls.LOWERCASE_PATTERN.search(password):
            errors.append("密码必须包含至少1个小写字母")
        
        # 检查数字
        if not cls.DIGIT_PATTERN.search(password):
            errors.append("密码必须包含至少1个数字")
        
        # 检查特殊字符
        if not cls.SPECIAL_PATTERN.search(password):
            errors.append("密码必须包含至少1个特殊字符 (!@#$%^&*等)")
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_strict(cls, password: str) -> Tuple[bool, List[str]]:
        """
        严格验证（额外检查常见弱密码）
        
        Args:
            password: 待验证的密码
            
        Returns:
            Tuple[bool, List[str]]: (是否通过, 错误列表)
        """
        # 先进行基本验证
        basic_pass, basic_errors = cls.validate(password)
        
        if not basic_pass:
            return False, basic_errors
        
        # 严格检查
        errors = []
        
        # 检查常见弱密码
        weak_passwords = [
            "password", "password123", "123456", "12345678",
            "qwerty", "abc123", "monkey", "master",
            "dragon", "letmein", "login", "admin",
        ]
        
        if password.lower() in weak_passwords:
            errors.append("请勿使用常见弱密码")
        
        # 检查重复字符过多（4个以上相同）
        if re.search(r'(.)\1{3,}', password):
            errors.append("密码不能包含4个以上重复的相同字符")
        
        # 检查连续字符（4个以上顺序或逆序）
        sequences = [
            "0123456789", "abcdefghijklmnopqrstuvwxyz",
            "qwertyuiop", "asdfghjkl", "zxcvbnm"
        ]
        password_lower = password.lower()
        for seq in sequences:
            for i in range(len(seq) - 3):
                pattern = seq[i:i+4]
                if pattern in password_lower or pattern[::-1] in password_lower:
                    errors.append("密码不能包含4个以上连续字符")
                    break
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_requirements(cls) -> List[str]:
        """
        获取密码要求列表
        
        Returns:
            List[str]: 密码要求描述列表
        """
        return [
            f"密码长度至少{cls.MIN_LENGTH}个字符",
            f"至少包含{cls.MIN_UPPERCASE}个大写字母 (A-Z)",
            f"至少包含{cls.MIN_LOWERCASE}个小写字母 (a-z)",
            f"至少包含{cls.MIN_DIGITS}个数字 (0-9)",
            f"至少包含{cls.MIN_SPECIAL}个特殊字符 ({cls.SPECIAL_CHARS[:5]}...)",
        ]


class PasswordStrength(Enum):
    """
    密码强度级别
    
    Attributes:
        VERY_WEAK: 非常弱
        WEAK: 弱
        FAIR: 一般
        MEDIUM: 中等
        STRONG: 强
        VERY_STRONG: 非常强
    """
    
    VERY_WEAK = 1
    WEAK = 2
    FAIR = 3
    MEDIUM = 4
    STRONG = 5
    VERY_STRONG = 6
    
    @classmethod
    def calculate(cls, password: str) -> "PasswordStrength":
        """
        计算密码强度
        
        基于多个因素计算密码强度得分：
        - 长度
        - 字符类型多样性
        - 熵值
        
        Args:
            password: 待计算的密码
            
        Returns:
            PasswordStrength: 密码强度级别
        """
        score = 0
        
        # 长度得分
        length = len(password)
        if length >= 8:
            score += 1
        if length >= 12:
            score += 1
        if length >= 16:
            score += 1
        if length >= 20:
            score += 1
        
        # 字符类型得分
        has_upper = bool(PasswordValidation.UPPERCASE_PATTERN.search(password))
        has_lower = bool(PasswordValidation.LOWERCASE_PATTERN.search(password))
        has_digit = bool(PasswordValidation.DIGIT_PATTERN.search(password))
        has_special = bool(PasswordValidation.SPECIAL_PATTERN.search(password))
        
        char_types = sum([has_upper, has_lower, has_digit, has_special])
        score += char_types
        
        # 基本验证是否通过
        is_valid, _ = PasswordValidation.validate(password)
        if not is_valid:
            # 如果连基本要求都不满足，强度最高为WEAK
            if score <= 2:
                return cls.VERY_WEAK
            else:
                return cls.WEAK
        
        # 根据得分确定强度
        if score <= 3:
            return cls.WEAK
        elif score <= 5:
            return cls.MEDIUM
        elif score <= 7:
            return cls.STRONG
        else:
            return cls.VERY_STRONG
    
    @property
    def description(self) -> str:
        """获取强度描述"""
        descriptions = {
            self.VERY_WEAK: "非常弱 - 容易被破解",
            self.WEAK: "弱 - 建议修改",
            self.FAIR: "一般 - 可以接受",
            self.MEDIUM: "中等 - 建议加强",
            self.STRONG: "强 - 符合要求",
            self.VERY_STRONG: "非常强 - 优秀",
        }
        return descriptions.get(self, "未知")
    
    @property
    def color(self) -> str:
        """获取强度颜色"""
        colors = {
            self.VERY_WEAK: "#dc3545",  # 红
            self.WEAK: "#fd7e14",       # 橙
            self.FAIR: "#ffc107",       # 黄
            self.MEDIUM: "#20c997",    # 青
            self.STRONG: "#28a745",     # 绿
            self.VERY_STRONG: "#198754", # 深绿
        }
        return colors.get(self, "#6c757d")
    
    @property
    def percentage(self) -> int:
        """获取强度百分比"""
        percentages = {
            self.VERY_WEAK: 15,
            self.WEAK: 30,
            self.FAIR: 45,
            self.MEDIUM: 60,
            self.STRONG: 80,
            self.VERY_STRONG: 100,
        }
        return percentages.get(self, 0)


class PasswordCheckResult:
    """
    密码检查结果
    
    用于封装密码验证和强度检测的完整结果。
    """
    
    def __init__(
        self,
        password: str,
        is_valid: bool,
        errors: List[str],
        strength: PasswordStrength
    ):
        self.password = password
        self.is_valid = is_valid
        self.errors = errors
        self.strength = strength
        self.strength_description = strength.description
        self.strength_percentage = strength.percentage
        self.strength_color = strength.color
    
    def to_dict(self) -> dict:
        """
        转换为字典
        
        Returns:
            dict: 结果字典
        """
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "strength": {
                "level": self.strength.name,
                "description": self.strength_description,
                "percentage": self.strength_percentage,
                "color": self.strength_color,
            },
            "requirements": PasswordValidation.get_requirements(),
        }
    
    @classmethod
    def check(cls, password: str, strict: bool = False) -> "PasswordCheckResult":
        """
        完整检查密码
        
        Args:
            password: 待检查的密码
            strict: 是否严格检查
            
        Returns:
            PasswordCheckResult: 检查结果
        """
        if strict:
            is_valid, errors = PasswordValidation.validate_strict(password)
        else:
            is_valid, errors = PasswordValidation.validate(password)
        
        strength = PasswordStrength.calculate(password)
        
        return cls(
            password=password,
            is_valid=is_valid,
            errors=errors,
            strength=strength
        )
