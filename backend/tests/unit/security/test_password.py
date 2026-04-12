"""
T-S3 密码复杂度验证 - 单元测试

测试目标：
1. PasswordValidation 密码验证
2. PasswordStrength 强度检测
3. 错误提示生成

Author: AI
Date: 2026-04-11
"""

import pytest
import re


class TestPasswordValidation:
    """测试密码验证"""

    def test_validate_min_length_pass(self):
        """测试最小长度-通过"""
        from app.schemas.password import PasswordValidation
        
        # 8字符，刚好通过
        result, errors = PasswordValidation.validate("Ab123456!")
        assert result is True
        assert len(errors) == 0

    def test_validate_min_length_fail(self):
        """测试最小长度-失败"""
        from app.schemas.password import PasswordValidation
        
        # 7字符，不满足
        result, errors = PasswordValidation.validate("Ab12345")
        assert result is False
        assert "最小8个字符" in str(errors)

    def test_validate_uppercase_pass(self):
        """测试大写字母-通过"""
        from app.schemas.password import PasswordValidation
        
        result, errors = PasswordValidation.validate("ABCdefg1!")
        assert result is True
        assert "大写字母" not in str(errors)

    def test_validate_uppercase_fail(self):
        """测试大写字母-失败"""
        from app.schemas.password import PasswordValidation
        
        result, errors = PasswordValidation.validate("abcdefg1!")
        assert result is False

    def test_validate_lowercase_pass(self):
        """测试小写字母-通过"""
        from app.schemas.password import PasswordValidation
        
        result, errors = PasswordValidation.validate("ABCDEFG1!")
        assert result is True

    def test_validate_lowercase_fail(self):
        """测试小写字母-失败"""
        from app.schemas.password import PasswordValidation
        
        result, errors = PasswordValidation.validate("ABCDEFG1!")
        assert result is False
        assert "小写字母" in str(errors)

    def test_validate_digit_pass(self):
        """测试数字-通过"""
        from app.schemas.password import PasswordValidation
        
        result, errors = PasswordValidation.validate("Abcdefg1!")
        assert result is True

    def test_validate_digit_fail(self):
        """测试数字-失败"""
        from app.schemas.password import PasswordValidation
        
        result, errors = PasswordValidation.validate("Abcdefgh!")
        assert result is False
        assert "数字" in str(errors)

    def test_validate_special_pass(self):
        """测试特殊字符-通过"""
        from app.schemas.password import PasswordValidation
        
        result, errors = PasswordValidation.validate("Abcdefg1!")
        assert result is True

    def test_validate_special_fail(self):
        """测试特殊字符-失败"""
        from app.schemas.password import PasswordValidation
        
        result, errors = PasswordValidation.validate("Abcdefg12")
        assert result is False
        assert "特殊字符" in str(errors)

    def test_validate_all_pass(self):
        """测试全部要求-通过"""
        from app.schemas.password import PasswordValidation
        
        # 满足所有要求
        test_cases = [
            "Abcdefg1!",
            "Password123@",
            "Admin!2024",
            "Secure#99Pass",
        ]
        
        for password in test_cases:
            result, errors = PasswordValidation.validate(password)
            assert result is True, f"Failed for {password}: {errors}"

    def test_validate_multiple_errors(self):
        """测试多个错误"""
        from app.schemas.password import PasswordValidation
        
        # 只有小写和数字
        result, errors = PasswordValidation.validate("abcdef123")
        assert result is False
        assert len(errors) >= 3  # 缺少大写、特殊字符，可能还有长度


class TestPasswordStrength:
    """测试密码强度检测"""

    def test_strength_weak(self):
        """测试弱密码"""
        from app.schemas.password import PasswordStrength
        
        # 仅满足最低要求
        strength = PasswordStrength.calculate("Abcdefg1")
        assert strength == PasswordStrength.Level.WEAK

    def test_strength_medium(self):
        """测试中等密码"""
        from app.schemas.password import PasswordStrength
        
        # 4项满足（排除一项）
        cases = [
            "ABCDEFG1!",  # 缺小写
            "abcdefg1!",  # 缺大写
            "Abcdefgh!",  # 缺数字
            "Abcdefg12",  # 缺特殊
        ]
        
        for pwd in cases:
            strength = PasswordStrength.calculate(pwd)
            assert strength == PasswordStrength.Level.MEDIUM, f"Failed for {pwd}"

    def test_strength_strong(self):
        """测试强密码"""
        from app.schemas.password import PasswordStrength
        
        # 全部满足
        cases = [
            "Abcdefg1!",
            "Password123@",
            "Secure#99Pass",
            "Test@1234Abc",
        ]
        
        for pwd in cases:
            strength = PasswordStrength.calculate(pwd)
            assert strength == PasswordStrength.Level.STRONG, f"Failed for {pwd}"

    def test_strength_very_strong(self):
        """测试非常强密码"""
        from app.schemas.password import PasswordStrength
        
        # 超过基本要求（更长+更多特殊字符）
        cases = [
            "Abcdefghijk1!@#",
            "VeryLongPassword123!@#$%",
        ]
        
        for pwd in cases:
            strength = PasswordStrength.calculate(pwd)
            # 可能是STRONG或VERY_STRONG
            assert strength in [PasswordStrength.Level.STRONG, PasswordStrength.Level.VERY_STRONG]


class TestErrorMessages:
    """测试错误消息生成"""

    def test_error_message_chinese(self):
        """测试中文错误消息"""
        from app.schemas.password import PasswordValidation
        
        result, errors = PasswordValidation.validate("abc")
        assert len(errors) > 0
        
        # 检查是否有中文错误信息
        error_str = str(errors)
        assert any('\u4e00' <= c <= '\u9fff' for c in error_str) or "字符" in error_str

    def test_error_message_detail(self):
        """测试详细错误消息"""
        from app.schemas.password import PasswordValidation
        
        result, errors = PasswordValidation.validate("ABCDEFG!")
        assert result is False
        
        # 应该指出缺少的内容
        assert len(errors) > 0


class TestEdgeCases:
    """边界测试"""

    def test_empty_password(self):
        """测试空密码"""
        from app.schemas.password import PasswordValidation
        
        result, errors = PasswordValidation.validate("")
        assert result is False
        assert len(errors) > 0

    def test_only_spaces(self):
        """测试纯空格密码"""
        from app.schemas.password import PasswordValidation
        
        result, errors = PasswordValidation.validate("        ")
        assert result is False

    def test_unicode_characters(self):
        """测试Unicode字符"""
        from app.schemas.password import PasswordValidation
        
        # 中文密码（应该也符合规则）
        result, errors = PasswordValidation.validate("密码Pass1!")
        # Unicode字母可能不被识别为大写/小写
        # 这里主要检查不崩溃

    def test_very_long_password(self):
        """测试超长密码"""
        from app.schemas.password import PasswordValidation
        
        long_pwd = "A" + "b" * 100 + "1" + "!"
        result, errors = PasswordValidation.validate(long_pwd)
        assert result is True

    def test_all_special_chars(self):
        """测试全特殊字符"""
        from app.schemas.password import PasswordValidation
        
        result, errors = PasswordValidation.validate("!@#$%^&*()")
        assert result is False

    def test_repeated_pattern(self):
        """测试重复模式"""
        from app.schemas.password import PasswordValidation
        
        # 重复字符
        result, errors = PasswordValidation.validate("Aaaaaaaa1!")
        # 可能通过（技术上满足要求）
        # 但强度应该是WEAK
        from app.schemas.password import PasswordStrength
        strength = PasswordStrength.calculate("Aaaaaaaa1!")
        assert strength == PasswordStrength.Level.WEAK


class TestPasswordConfig:
    """测试密码配置"""

    def test_config_values(self):
        """测试配置值"""
        from app.schemas.password import PasswordValidation
        
        assert PasswordValidation.MIN_LENGTH == 8
        assert PasswordValidation.MIN_UPPERCASE == 1
        assert PasswordValidation.MIN_LOWERCASE == 1
        assert PasswordValidation.MIN_DIGITS == 1
        assert PasswordValidation.MIN_SPECIAL == 1

    def test_special_chars_list(self):
        """测试特殊字符列表"""
        from app.schemas.password import PasswordValidation
        
        assert "!" in PasswordValidation.SPECIAL_CHARS
        assert "@" in PasswordValidation.SPECIAL_CHARS
        assert len(PasswordValidation.SPECIAL_CHARS) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
