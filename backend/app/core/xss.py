"""
XSS防护核心

提供XSS过滤和编码功能，符合三级等保要求：
- 8.1.2.3 安全审计：输入验证
- 8.1.4.2 入侵防范：防止XSS攻击

Author: AI
Date: 2026-04-11
"""

import re
import html
from typing import Set, List


class XSSConfig:
    """XSS防护配置"""
    
    # 危险标签
    DANGEROUS_TAGS: Set[str] = {
        "script", "iframe", "object", "embed", "applet",
        "form", "input", "button", "select", "textarea",
        "base", "basefont", "link", "meta", "style",
        "svg", "math", "xml", "xmp", "bgsound",
    }
    
    # 危险属性
    DANGEROUS_ATTRS: Set[str] = {
        "onload", "onerror", "onclick", "onmouseover", "onmouseout",
        "onfocus", "onblur", "onchange", "onsubmit", "onreset",
        "onselect", "onkeydown", "onkeyup", "onkeypress", "ondblclick",
        "onabort", "ondragdrop", "onhashchange", "onmessage", "onpopstate",
        "onstorage", "onbeforeunload", "onunload", "onresize", "onscroll",
    }
    
    # 危险协议
    DANGEROUS_PROTOCOLS: Set[str] = {
        "javascript", "vbscript", "data", "livescript",
    }
    
    # 过滤级别
    class Level:
        STRICT = "strict"    # 严格：移除所有危险内容
        RELAXED = "relaxed"  # 宽松：保留部分格式
        NONE = "none"        # 不过滤
    
    # 默认级别
    DEFAULT_LEVEL = "strict"


class XSSFilter:
    """
    XSS过滤器
    
    提供输入过滤和输出编码功能。
    """
    
    def __init__(self, level: str = XSSConfig.DEFAULT_LEVEL):
        """
        初始化过滤器
        
        Args:
            level: 过滤级别
        """
        self.level = level
    
    def filter_input(self, text: str) -> str:
        """
        过滤危险输入
        
        Args:
            text: 输入文本
            
        Returns:
            str: 过滤后的文本
        """
        if not text:
            return text
        
        if self.level == XSSConfig.Level.NONE:
            return text
        
        result = text
        
        if self.level == XSSConfig.Level.STRICT:
            # 移除HTML标签
            result = self._remove_tags(result)
            # 移除危险属性
            result = self._remove_dangerous_attrs(result)
            # 移除危险协议
            result = self._remove_dangerous_protocols(result)
        
        elif self.level == XSSConfig.Level.RELAXED:
            # 只移除最危险的标签
            result = self._remove_script_tags(result)
            # 移除on*事件
            result = self._remove_event_handlers(result)
        
        return result
    
    def _remove_tags(self, text: str) -> str:
        """移除所有HTML标签"""
        # 移除标签
        text = re.sub(r'<[^>]*>', '', text)
        # 移除注释
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        return text
    
    def _remove_script_tags(self, text: str) -> str:
        """移除script标签"""
        # 移除<script>标签
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        # 移除<script />
        text = re.sub(r'<script[^>]*/?\s*>', '', text, flags=re.IGNORECASE)
        return text
    
    def _remove_dangerous_attrs(self, text: str) -> str:
        """移除危险属性"""
        for attr in XSSConfig.DANGEROUS_ATTRS:
            # 移除 onxxx="..."
            text = re.sub(rf'\s*{attr}\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
            # 移除 onxxx='...'
            text = re.sub(rf'\s*{attr}\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
            # 移除 onxxx=...
            text = re.sub(rf'\s*{attr}\s*=\s*[^\s>]*', '', text, flags=re.IGNORECASE)
        return text
    
    def _remove_event_handlers(self, text: str) -> str:
        """移除事件处理器"""
        return self._remove_dangerous_attrs(text)
    
    def _remove_dangerous_protocols(self, text: str) -> str:
        """移除危险协议"""
        for protocol in XSSConfig.DANGEROUS_PROTOCOLS:
            # javascript:
            text = re.sub(
                rf':\s*{protocol}\s*:',
                ':safe:',
                text,
                flags=re.IGNORECASE
            )
            # href="javascript:..."
            text = re.sub(
                rf'(href|src|action)\s*=\s*["\']?\s*{protocol}\s*:',
                rf'\1="safe:',
                text,
                flags=re.IGNORECASE
            )
        return text


class XSSEncoder:
    """
    XSS编码器
    
    根据不同上下文对输出进行安全编码。
    """
    
    @staticmethod
    def encode_html(text: str) -> str:
        """
        HTML上下文编码
        
        Args:
            text: 文本
            
        Returns:
            str: 编码后的文本
        """
        return html.escape(text, quote=True)
    
    @staticmethod
    def encode_html_attr(text: str) -> str:
        """
        HTML属性上下文编码
        
        Args:
            text: 文本
            
        Returns:
            str: 编码后的文本
        """
        text = html.escape(text, quote=True)
        # 额外编码空格
        text = text.replace(' ', '%20')
        return text
    
    @staticmethod
    def encode_javascript(text: str) -> str:
        """
        JavaScript上下文编码
        
        Args:
            text: 文本
            
        Returns:
            str: 编码后的文本
        """
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        text = text.replace("'", "\\'")
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        text = text.replace('<', '\\x3c')
        text = text.replace('>', '\\x3e')
        return text
    
    @staticmethod
    def encode_url(text: str) -> str:
        """
        URL上下文编码
        
        Args:
            text: 文本
            
        Returns:
            str: 编码后的文本
        """
        from urllib.parse import quote
        return quote(text, safe='')
    
    @staticmethod
    def encode_css(text: str) -> str:
        """
        CSS上下文编码
        
        Args:
            text: 文本
            
        Returns:
            str: 编码后的文本
        """
        # 转义特殊字符
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        text = text.replace("'", "\\'")
        text = text.replace('<', '\\3c ')
        text = text.replace('>', '\\3e ')
        # 移除非ASCII字符
        text = ''.join(c if ord(c) < 128 else '' for c in text)
        return text
    
    @classmethod
    def encode(cls, text: str, context: str = 'html') -> str:
        """
        根据上下文编码
        
        Args:
            text: 文本
            context: 上下文类型 (html, attr, js, url, css)
            
        Returns:
            str: 编码后的文本
        """
        encoders = {
            'html': cls.encode_html,
            'attr': cls.encode_html_attr,
            'attribute': cls.encode_html_attr,
            'javascript': cls.encode_javascript,
            'js': cls.encode_javascript,
            'url': cls.encode_url,
            'css': cls.encode_css,
        }
        
        encoder = encoders.get(context.lower(), cls.encode_html)
        return encoder(text)


# 全局默认过滤器
_default_filter = XSSFilter()


def filter_input(text: str, level: str = None) -> str:
    """
    全局输入过滤函数
    
    Args:
        text: 输入文本
        level: 过滤级别
        
    Returns:
        str: 过滤后的文本
    """
    if level:
        filter_obj = XSSFilter(level)
        return filter_obj.filter_input(text)
    return _default_filter.filter_input(text)


def encode_output(text: str, context: str = 'html') -> str:
    """
    全局输出编码函数
    
    Args:
        text: 输出文本
        context: 上下文类型
        
    Returns:
        str: 编码后的文本
    """
    return XSSEncoder.encode(text, context)
