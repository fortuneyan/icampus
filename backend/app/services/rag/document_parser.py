"""
Document Parser - 文档解析服务

支持解析多种文档格式:
- PDF (.pdf)
- Word (.docx, .doc)
- Text (.txt)
- Markdown (.md)

用法:
    from app.services.rag.document_parser import DocumentParser

    parser = DocumentParser()

    # 解析文件
    sections = await parser.parse_file("/path/to/document.pdf")

    # 解析文本
    sections = await parser.parse_text("文本内容", "text")
"""

import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DocumentSection:
    """文档段落"""

    title: str
    content: str
    level: int = 1
    page: Optional[int] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_text(self) -> str:
        """转换为文本"""
        if self.title:
            return f"{self.title}\n{self.content}"
        return self.content


class DocumentParser:
    """文档解析器"""

    def __init__(self):
        self._pdf_parser = None
        self._docx_parser = None

    async def parse_file(
        self,
        file_path: str,
        max_length: int = 1000,
    ) -> List[DocumentSection]:
        """
        解析文档文件

        Args:
            file_path: 文件路径
            max_length: 每个段落最大字符数

        Returns:
            段落列表
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            return await self._parse_pdf(file_path, max_length)
        elif ext in [".docx", ".doc"]:
            return await self._parse_docx(file_path, max_length)
        elif ext in [".txt", ".md"]:
            return await self._parse_text_file(file_path, max_length)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    async def parse_text(
        self,
        text: str,
        source: str = "text",
        max_length: int = 1000,
    ) -> List[DocumentSection]:
        """
        解析文本内容

        Args:
            text: 文本内容
            source: 来源标识
            max_length: 每个段落最大字符数

        Returns:
            段落列表
        """
        sections = []

        # 按行分割
        lines = text.split("\n")
        current_section = None
        current_content = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测标题
            if self._is_title(line):
                # 保存之前的段落
                if current_content:
                    content = " ".join(current_content)
                    if len(content) > max_length:
                        # 分段
                        chunks = self._split_long_text(content, max_length)
                        for i, chunk in enumerate(chunks):
                            sections.append(
                                DocumentSection(
                                    title=current_section or source,
                                    content=chunk,
                                    level=1 if current_section else 2,
                                )
                            )
                    else:
                        sections.append(
                            DocumentSection(
                                title=current_section or source,
                                content=content,
                                level=1 if current_section else 2,
                            )
                        )
                    current_content = []

                # 设置新标题
                level = self._get_title_level(line)
                current_section = self._clean_title(line)

            else:
                current_content.append(line)

        # 保存最后一段
        if current_content:
            content = " ".join(current_content)
            if content:
                if len(content) > max_length:
                    chunks = self._split_long_text(content, max_length)
                    for chunk in chunks:
                        sections.append(
                            DocumentSection(
                                title=current_section or source,
                                content=chunk,
                                level=1 if current_section else 2,
                            )
                        )
                else:
                    sections.append(
                        DocumentSection(
                            title=current_section or source,
                            content=content,
                            level=1 if current_section else 2,
                        )
                    )

        return sections

    def _is_title(self, line: str) -> bool:
        """检测是否是标题"""
        # Markdown标题
        if line.startswith("#"):
            return True
        # 数字序号标题 1. 2.
        if re.match(r"^\d+\.\s+", line):
            return True
        # 字母序号 A. B.
        if re.match(r"^[A-Z]\.\s+", line):
            return True
        # 短标题且全大写
        if len(line) < 100 and line.isupper():
            return True
        return False

    def _get_title_level(self, line: str) -> int:
        """获取标题级别"""
        # Markdown级别
        if line.startswith("###"):
            return 3
        if line.startswith("##"):
            return 2
        if line.startswith("#"):
            return 1
        return 2

    def _clean_title(self, line: str) -> str:
        """清理标题"""
        # 移除Markdown符号
        line = re.sub(r"^#+\s*", "", line)
        # 移除序号
        line = re.sub(r"^\d+\.\s*", "", line)
        line = re.sub(r"^[A-Z]\.\s*", "", line)
        return line.strip()

    def _split_long_text(self, text: str, max_length: int) -> List[str]:
        """拆分长文本"""
        chunks = []
        paragraphs = text.split("\n\n")
        current = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current) + len(para) <= max_length:
                current += para + "\n"
            else:
                if current:
                    chunks.append(current.strip())
                current = para + "\n"

        if current:
            chunks.append(current.strip())

        return chunks if chunks else [text]

    async def _parse_pdf(
        self,
        file_path: str,
        max_length: int,
    ) -> List[DocumentSection]:
        """解析PDF"""
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("pypdf not installed. Run: pip install pypdf")

        reader = PdfReader(file_path)
        sections = []

        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()

            # 简单按页解析
            page_sections = await self.parse_text(
                text,
                source=f"page_{page_num}",
                max_length=max_length,
            )

            for section in page_sections:
                section.page = page_num
                sections.append(section)

        return sections

    async def _parse_docx(
        self,
        file_path: str,
        max_length: int,
    ) -> List[DocumentSection]:
        """解析Word文档"""
        try:
            from docx import Document
        except ImportError:
            raise ImportError("python-docx not installed. Run: pip install python-docx")

        doc = Document(file_path)
        sections = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # 检测是否是标题
            if para.style.name.startswith("Heading"):
                level = int(para.style.name.replace("Heading ", "")) or 1
                sections.append(
                    DocumentSection(
                        title=text,
                        content="",
                        level=level,
                    )
                )
            else:
                # 内容
                if sections and sections[-1].content:
                    sections[-1].content += "\n" + text
                elif sections:
                    sections[-1].content = text
                else:
                    sections.append(
                        DocumentSection(
                            title="",
                            content=text,
                            level=2,
                        )
                    )

        return sections

    async def _parse_text_file(
        self,
        file_path: str,
        max_length: int,
    ) -> List[DocumentSection]:
        """解析文本文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        return await self.parse_text(
            text,
            source=os.path.basename(file_path),
            max_length=max_length,
        )


# 全局单例
_document_parser: Optional[DocumentParser] = None


def get_document_parser() -> DocumentParser:
    """获取全局文档解析器"""
    global _document_parser
    if _document_parser is None:
        _document_parser = DocumentParser()
    return _document_parser
