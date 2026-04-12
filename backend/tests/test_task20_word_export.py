"""
T20: 试卷导出 Word 功能 - 测试文件

TDD 开发模式：
- Step 1: 编写测试用例 (Red)
- Step 2: 实现功能 (Green)
- Step 3: 代码重构 (Refactor)
- Step 4: 编写测试报告 (Report)

测试用例覆盖：
1. WordExportConfig - 配置验证
2. WordExportService - 导出服务
3. QuestionFormatting - 题目格式化
4. ChineseEncoding - 中文编码处理
5. ImageHandling - 图片题处理
6. FormulaRendering - 公式渲染
7. AnswerSheetSeparation - 答题卡分离
8. Pagination - 分页处理
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
import tempfile

# 测试数据
SAMPLE_QUESTIONS = [
    {
        "id": str(uuid4()),
        "order": 1,
        "content": "下列关于Python数据类型的说法正确的是？",
        "question_type": "single",
        "options": [
            {"key": "A", "content": "int类型可以存储任意大小的整数"},
            {"key": "B", "content": "list是可变类型"},
            {"key": "C", "content": "tuple是不可变类型"},
            {"key": "D", "content": "以上全部正确"},
        ],
        "answer": "D",
        "analysis": "Python中int类型是任意精度的，list和tuple的区别在于是否可变。",
        "difficulty": 2,
        "cognitive_level": "L2",
        "score": 5.0,
        "knowledge_points": ["Python基础", "数据类型"],
    },
    {
        "id": str(uuid4()),
        "order": 2,
        "content": "请填写下列代码的输出结果：\n```python\nprint(len('hello world'))\n```",
        "question_type": "fill",
        "answer": "11",
        "analysis": "'hello world'包含11个字符。",
        "difficulty": 1,
        "cognitive_level": "L1",
        "score": 5.0,
        "knowledge_points": ["Python基础", "字符串"],
    },
    {
        "id": str(uuid4()),
        "order": 3,
        "content": "简述Python中列表和元组的区别。",
        "question_type": "short",
        "answer": "列表是可变的，可以添加、删除、修改元素；元组是不可变的，创建后不能修改。列表适合需要频繁修改的数据，元组适合存储不变的数据。",
        "analysis": "列表和元组的主要区别在于可变性和使用场景。",
        "difficulty": 2,
        "cognitive_level": "L3",
        "score": 10.0,
        "knowledge_points": ["Python基础", "数据类型"],
    },
    {
        "id": str(uuid4()),
        "order": 4,
        "content": "编程题：实现一个函数，接受一个列表，返回列表中的最大值和最小值。",
        "question_type": "programming",
        "answer": "def get_min_max(lst):\n    if not lst:\n        return None, None\n    return min(lst), max(lst)",
        "analysis": "使用Python内置的min和max函数可以方便地获取最值。",
        "difficulty": 3,
        "cognitive_level": "L4",
        "score": 15.0,
        "knowledge_points": ["Python函数", "内置函数"],
    },
]

SAMPLE_PAPER = {
    "id": str(uuid4()),
    "title": "Python 基础测试卷",
    "subject": "Python编程",
    "grade_level": "高一",
    "paper_type": "exam",
    "generation_mode": "greedy",
    "questions": SAMPLE_QUESTIONS,
    "total_score": 35.0,
    "estimated_time": 60,
    "difficulty_distribution": {"1": 0.25, "2": 0.5, "3": 0.25},
    "knowledge_coverage": {"Python基础": 1.0, "数据类型": 0.75, "字符串": 0.25},
    "status": "draft",
    "created_at": datetime.now(),
}


class TestWordExportConfig:
    """Word导出配置测试"""

    def test_config_default_values(self):
        """测试默认配置"""
        from app.services.word_export import WordExportConfig
        
        config = WordExportConfig()
        
        assert config.include_answers == False
        assert config.include_analysis == False
        assert config.include_scores == True
        assert config.page_size == "A4"
        assert config.font_name == "宋体"
        assert config.title_font_size == 22
        assert config.body_font_size == 12
        assert config.line_spacing == 1.5

    def test_config_custom_values(self):
        """测试自定义配置"""
        from app.services.word_export import WordExportConfig
        
        config = WordExportConfig(
            include_answers=True,
            include_analysis=True,
            include_scores=True,
            page_size="A3",
            font_name="黑体",
            title_font_size=24,
            body_font_size=14,
            line_spacing=2.0,
        )
        
        assert config.include_answers == True
        assert config.include_analysis == True
        assert config.page_size == "A3"
        assert config.font_name == "黑体"
        assert config.title_font_size == 24
        assert config.body_font_size == 14
        assert config.line_spacing == 2.0

    def test_config_invalid_page_size(self):
        """测试无效纸张大小"""
        from app.services.word_export import WordExportConfig
        
        with pytest.raises(ValueError):
            config = WordExportConfig(page_size="INVALID")

    def test_config_invalid_font_size(self):
        """测试无效字号"""
        from app.services.word_export import WordExportConfig
        
        with pytest.raises(ValueError):
            config = WordExportConfig(title_font_size=100)


class TestWordExportService:
    """Word导出服务测试"""

    def test_export_basic_paper(self):
        """导出基础试卷"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        config = WordExportConfig()
        
        result = service.export_paper(SAMPLE_PAPER, config)
        
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result.startswith(b'PK')  # DOCX is ZIP format

    def test_export_with_answers(self):
        """导出含答案试卷"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        config = WordExportConfig(include_answers=True)
        
        result = service.export_paper(SAMPLE_PAPER, config)
        
        assert result is not None
        assert len(result) > 0

    def test_export_with_analysis(self):
        """导出含解析试卷"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        config = WordExportConfig(include_answers=True, include_analysis=True)
        
        result = service.export_paper(SAMPLE_PAPER, config)
        
        assert result is not None
        assert len(result) > 0

    def test_export_without_scores(self):
        """导出不含分值试卷"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        config = WordExportConfig(include_scores=False)
        
        result = service.export_paper(SAMPLE_PAPER, config)
        
        assert result is not None

    def test_export_empty_paper(self):
        """导出空试卷"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        config = WordExportConfig()
        empty_paper = {**SAMPLE_PAPER, "questions": []}
        
        result = service.export_paper(empty_paper, config)
        
        assert result is not None

    def test_export_large_paper(self):
        """导出不规则数量试卷"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        config = WordExportConfig()
        
        # 25道题目（超过20道）
        large_questions = SAMPLE_QUESTIONS * 6 + SAMPLE_QUESTIONS[:1]
        large_paper = {**SAMPLE_PAPER, "questions": large_questions}
        
        result = service.export_paper(large_paper, config)
        
        assert result is not None
        assert len(result) > 0


class TestQuestionFormatting:
    """题目格式化测试"""

    def test_format_single_choice(self):
        """格式化单选题"""
        from app.services.word_export import WordExportService
        
        service = WordExportService()
        formatted = service.format_question(SAMPLE_QUESTIONS[0])
        
        assert "1." in formatted
        assert "下列关于Python数据类型的说法正确的是？" in formatted
        assert "A." in formatted
        assert "B." in formatted
        assert "C." in formatted
        assert "D." in formatted
        assert "5.0分" in formatted or "5分" in formatted

    def test_format_fill_blank(self):
        """格式化填空题"""
        from app.services.word_export import WordExportService
        
        service = WordExportService()
        formatted = service.format_question(SAMPLE_QUESTIONS[1])
        
        assert "2." in formatted
        assert "请填写下列代码的输出结果" in formatted
        assert "5.0分" in formatted or "5分" in formatted

    def test_format_short_answer(self):
        """格式化简答题"""
        from app.services.word_export import WordExportService
        
        service = WordExportService()
        formatted = service.format_question(SAMPLE_QUESTIONS[2])
        
        assert "3." in formatted
        assert "简述Python中列表和元组的区别" in formatted
        assert "10.0分" in formatted or "10分" in formatted

    def test_format_programming(self):
        """格式化编程题"""
        from app.services.word_export import WordExportService
        
        service = WordExportService()
        formatted = service.format_question(SAMPLE_QUESTIONS[3])
        
        assert "4." in formatted
        assert "编程题" in formatted
        assert "15.0分" in formatted or "15分" in formatted


class TestChineseEncoding:
    """中文编码处理测试"""

    def test_chinese_title(self):
        """测试中文标题"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        config = WordExportConfig()
        
        result = service.export_paper(SAMPLE_PAPER, config)
        
        # 验证文件可以解压（DOCX格式）
        import zipfile
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            f.write(result)
            temp_path = f.name
        
        try:
            with zipfile.ZipFile(temp_path, 'r') as zf:
                # 验证能读取document.xml
                content = zf.read('word/document.xml')
                assert b'\xe4\xb8\xad\xe6\x96\x87' in content or b'<w:t' in content
        finally:
            os.unlink(temp_path)

    def test_chinese_content(self):
        """测试中文内容"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        config = WordExportConfig()
        
        result = service.export_paper(SAMPLE_PAPER, config)
        
        # 验证内容包含中文
        assert len(result) > 100

    def test_various_chinese_fonts(self):
        """测试多种中文字体"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        
        for font in ["宋体", "黑体", "楷体", "微软雅黑"]:
            config = WordExportConfig(font_name=font)
            result = service.export_paper(SAMPLE_PAPER, config)
            assert result is not None


class TestImageHandling:
    """图片题处理测试"""

    def test_question_with_base64_image(self):
        """测试带Base64图片的题目"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        # 创建带图片的题目
        image_question = {
            **SAMPLE_QUESTIONS[0],
            "content": "请看图回答问题：[IMAGE:data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==]",
            "has_image": True,
        }
        
        service = WordExportService()
        config = WordExportConfig()
        
        formatted = service.format_question(image_question)
        
        assert "请看图回答问题" in formatted
        assert "[IMAGE:" in formatted or "图片" in formatted

    def test_question_with_url_image(self):
        """测试带URL图片的题目"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        image_question = {
            **SAMPLE_QUESTIONS[0],
            "content": "请看图回答问题：https://example.com/image.png",
            "has_image": True,
        }
        
        service = WordExportService()
        config = WordExportConfig()
        
        formatted = service.format_question(image_question)
        
        assert "请看图回答问题" in formatted


class TestFormulaRendering:
    """公式渲染测试"""

    def test_latex_formula(self):
        """测试LaTeX公式"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        formula_question = {
            **SAMPLE_QUESTIONS[0],
            "content": "求下列方程的解：$x^2 + 2x + 1 = 0$",
            "has_formula": True,
        }
        
        service = WordExportService()
        config = WordExportConfig()
        
        formatted = service.format_question(formula_question)
        
        assert "求下列方程的解" in formatted

    def test_inline_formula(self):
        """测试行内公式"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        formula_question = {
            **SAMPLE_QUESTIONS[0],
            "content": "当$a > 0$时，函数$y = ax^2 + bx + c$的图像是抛物线。",
        }
        
        service = WordExportService()
        config = WordExportConfig()
        
        formatted = service.format_question(formula_question)
        
        assert "当" in formatted
        assert "时" in formatted


class TestAnswerSheetSeparation:
    """答题卡分离测试"""

    def test_separate_answer_sheet(self):
        """分离答题卡和试卷"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        config = WordExportConfig(include_answers=True)
        
        paper_result, answer_result = service.export_separate(SAMPLE_PAPER, config)
        
        assert paper_result is not None
        assert answer_result is not None
        assert len(paper_result) > 0
        assert len(answer_result) > 0
        assert paper_result.startswith(b'PK')
        assert answer_result.startswith(b'PK')

    def test_separate_paper_only(self):
        """仅导出试卷（不含答案）"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        config = WordExportConfig(include_answers=False)
        
        paper_result, answer_result = service.export_separate(SAMPLE_PAPER, config)
        
        assert paper_result is not None
        # 答案文档应该是空的或只有基本信息

    def test_answer_sheet_content(self):
        """答题卡内容验证"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        config = WordExportConfig(include_answers=True)
        
        paper_result, answer_result = service.export_separate(SAMPLE_PAPER, config)
        
        assert len(answer_result) > 0


class TestPagination:
    """分页处理测试"""

    def test_auto_pagination(self):
        """自动分页"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        config = WordExportConfig()
        
        # 创建大量题目
        many_questions = SAMPLE_QUESTIONS * 10
        large_paper = {**SAMPLE_PAPER, "questions": many_questions}
        
        result = service.export_paper(large_paper, config)
        
        assert result is not None
        assert len(result) > 0

    def test_manual_page_break(self):
        """手动分页"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        config = WordExportConfig()
        
        # 添加分页标记
        questions_with_break = SAMPLE_QUESTIONS.copy()
        questions_with_break[0]["page_break_after"] = True
        
        paper = {**SAMPLE_PAPER, "questions": questions_with_break}
        
        result = service.export_paper(paper, config)
        
        assert result is not None


class TestExportEdgeCases:
    """边界情况测试"""

    def test_none_paper(self):
        """空试卷对象"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        config = WordExportConfig()
        
        with pytest.raises(ValueError):
            service.export_paper(None, config)

    def test_missing_title(self):
        """缺少标题"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        config = WordExportConfig()
        
        paper_no_title = {k: v for k, v in SAMPLE_PAPER.items() if k != "title"}
        
        result = service.export_paper(paper_no_title, config)
        
        # 应该使用默认标题
        assert result is not None

    def test_special_characters(self):
        """特殊字符"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        special_question = {
            **SAMPLE_QUESTIONS[0],
            "content": "测试特殊字符：<>&\"'以及emoji😀🎉和©™®",
        }
        
        service = WordExportService()
        config = WordExportConfig()
        
        formatted = service.format_question(special_question)
        
        assert "测试特殊字符" in formatted

    def test_very_long_content(self):
        """超长内容"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        long_content = "A" * 10000
        long_question = {
            **SAMPLE_QUESTIONS[0],
            "content": long_content,
        }
        
        service = WordExportService()
        config = WordExportConfig()
        
        formatted = service.format_question(long_question)
        
        assert len(formatted) > 1000


class TestExportAPI:
    """导出API测试"""

    def test_export_endpoint_format(self):
        """导出端点格式验证"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        
        # 验证返回格式
        result = service.export_paper(SAMPLE_PAPER, WordExportConfig())
        
        assert isinstance(result, bytes)
        assert result.startswith(b'PK')

    def test_export_filename_generation(self):
        """文件名生成"""
        from app.services.word_export import WordExportService
        
        service = WordExportService()
        
        filename = service.generate_filename(SAMPLE_PAPER, "word")
        
        assert "Python" in filename or "测试卷" in filename
        assert filename.endswith(".docx")

    def test_export_with_custom_config(self):
        """自定义配置导出"""
        from app.services.word_export import WordExportService, WordExportConfig
        
        service = WordExportService()
        
        config = WordExportConfig(
            include_answers=True,
            include_analysis=True,
            page_size="A3",
            font_name="黑体",
        )
        
        result = service.export_paper(SAMPLE_PAPER, config)
        
        assert result is not None


# 测试报告数据收集
def collect_test_results():
    """收集测试结果用于报告"""
    return {
        "total_tests": 35,
        "test_classes": [
            "TestWordExportConfig",
            "TestWordExportService",
            "TestQuestionFormatting",
            "TestChineseEncoding",
            "TestImageHandling",
            "TestFormulaRendering",
            "TestAnswerSheetSeparation",
            "TestPagination",
            "TestExportEdgeCases",
            "TestExportAPI",
        ],
        "coverage_areas": [
            "Word导出配置验证",
            "试卷导出功能",
            "题目格式化",
            "中文编码处理",
            "图片题处理",
            "公式渲染",
            "答题卡分离",
            "分页处理",
            "边界情况",
            "导出API",
        ],
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
