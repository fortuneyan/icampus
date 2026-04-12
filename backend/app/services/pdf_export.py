"""
试卷导出 PDF 服务

使用 reportlab 库生成高质量 PDF 文件，支持：
- 多种页面大小（A4, A3, Letter, Legal）
- 横向/纵向布局
- 中文字体支持
- 答题卡分离导出
- 分值和答案显示控制
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from io import BytesIO
import os

# PDF 库导入（可选）
try:
    from reportlab.lib.pagesizes import A4, A3, letter, legal
    from reportlab.lib.units import inch, mm
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# ============================================================================
# 配置类
# ============================================================================

@dataclass
class PDFExportConfig:
    """PDF导出配置"""
    include_answers: bool = False           # 包含答案
    include_analysis: bool = False         # 包含解析
    include_scores: bool = True            # 包含分值
    page_size: str = "A4"                  # 纸张大小
    orientation: str = "portrait"           # 方向: portrait/landscape
    font_name: str = "STSong-Light"         # 字体名称
    title_font_size: int = 18              # 标题字号
    body_font_size: int = 10                # 正文字号
    line_spacing: float = 1.5              # 行间距
    margin_top: float = 72                 # 上边距 (points)
    margin_bottom: float = 72              # 下边距
    margin_left: float = 72                # 左边距
    margin_right: float = 72               # 右边距
    include_answer_sheet: bool = False     # 包含答题卡
    answer_sheet_position: str = "end"      # 答题卡位置: begin/end/separate
    
    # 内部状态
    _current_page: int = field(default=0, init=False, repr=False)
    _content_width: float = field(default=0.0, init=False, repr=False)
    _content_height: float = field(default=0.0, init=False, repr=False)
    
    def __post_init__(self):
        """验证配置参数"""
        # 验证 page_size
        valid_sizes = ["A4", "A3", "Letter", "Legal"]
        if self.page_size not in valid_sizes:
            raise ValueError(f"Invalid page_size: {self.page_size}. Must be one of {valid_sizes}")
        
        # 验证 orientation
        if self.orientation not in ["portrait", "landscape"]:
            raise ValueError(f"Invalid orientation: {self.orientation}. Must be portrait or landscape")
        
        # 验证字体
        valid_fonts = ["STSong-Light", "STHeiti-Regular", "STKaiti-Regular", 
                       "SimSun", "SimHei", "Arial", "Helvetica"]
        if self.font_name not in valid_fonts:
            raise ValueError(f"Invalid font_name: {self.font_name}")
        
        # 验证字号范围
        if not (8 <= self.title_font_size <= 32):
            raise ValueError(f"title_font_size must be between 8 and 32, got {self.title_font_size}")
        if not (8 <= self.body_font_size <= 20):
            raise ValueError(f"body_font_size must be between 8 and 20, got {self.body_font_size}")
        
        # 验证边距
        if self.margin_top < 36 or self.margin_bottom < 36:
            raise ValueError("Margins must be at least 0.5 inch (36 points)")
        
        # 验证 answer_sheet_position
        if self.answer_sheet_position not in ["begin", "end", "separate"]:
            raise ValueError(f"Invalid answer_sheet_position: {self.answer_sheet_position}")
    
    def get_page_size_tuple(self) -> Tuple[float, float]:
        """获取页面大小元组"""
        sizes = {
            "A4": A4,
            "A3": A3,
            "Letter": letter,
            "Legal": legal
        }
        
        size = sizes.get(self.page_size, A4)
        
        if self.orientation == "landscape":
            # 交换宽高
            return (size[1], size[0])
        return size
    
    def calculate_content_area(self) -> Tuple[float, float]:
        """计算内容区域大小"""
        page_width, page_height = self.get_page_size_tuple()
        
        content_width = page_width - self.margin_left - self.margin_right
        content_height = page_height - self.margin_top - self.margin_bottom
        
        self._content_width = content_width
        self._content_height = content_height
        
        return content_width, content_height


# ============================================================================
# PDF 导出服务
# ============================================================================

class PDFExportService:
    """PDF 导出服务"""
    
    # 题号前缀映射
    QUESTION_PREFIXES = {
        "single": "一、选择题",
        "multiple": "二、多选题",
        "fill": "三、填空题",
        "short": "四、简答题",
        "programming": "五、编程题",
        "discussion": "六、论述题",
        "material": "七、材料题"
    }
    
    def __init__(self, config: Optional[PDFExportConfig] = None):
        """初始化导出服务"""
        self.config = config or PDFExportConfig()
        self._buffer: Optional[BytesIO] = None
        self._canvas = None
    
    def export_paper(
        self, 
        paper: Dict[str, Any], 
        output_path: Optional[str] = None
    ) -> BytesIO:
        """
        导出试卷为 PDF 格式
        
        Args:
            paper: 试卷数据
            output_path: 输出文件路径（可选）
            
        Returns:
            BytesIO: PDF 文件缓冲区
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "reportlab is required for PDF export. "
                "Please install it with: pip install reportlab"
            )
        
        # 创建缓冲区
        self._buffer = BytesIO()
        
        # 创建画布
        self._canvas = canvas.Canvas(
            self._buffer, 
            pagesize=self.config.get_page_size_tuple()
        )
        
        # 注册中文字体
        self._register_fonts()
        
        # 绘制试卷内容
        self._draw_paper_content(paper)
        
        # 如果需要答题卡
        if self.config.include_answer_sheet:
            if self.config.answer_sheet_position == "end":
                self._draw_answer_sheet(paper)
        
        # 保存 PDF
        self._canvas.save()
        
        # 如果指定了输出路径，写入文件
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(self._buffer.getvalue())
        
        self._buffer.seek(0)
        return self._buffer
    
    def export_separate(
        self, 
        paper: Dict[str, Any]
    ) -> Tuple[BytesIO, BytesIO]:
        """
        分离导出试卷和答题卡
        
        Returns:
            Tuple[BytesIO, BytesIO]: (试卷PDF, 答题卡PDF)
        """
        # 导出试卷
        paper_buffer = self.export_paper(paper)
        
        # 导出答题卡
        answer_config = PDFExportConfig(
            page_size=self.config.page_size,
            orientation=self.config.orientation,
            font_name=self.config.font_name
        )
        
        answer_service = PDFExportService(answer_config)
        answer_buffer = BytesIO()
        
        canvas = canvas.Canvas(
            answer_buffer,
            pagesize=answer_config.get_page_size_tuple()
        )
        
        # 绘制答题卡
        self._draw_answer_sheet_content(canvas, paper)
        canvas.save()
        
        answer_buffer.seek(0)
        
        return paper_buffer, answer_buffer
    
    def _register_fonts(self):
        """注册字体"""
        # 尝试注册中文字体
        font_paths = [
            # Windows 字体路径
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/STSONG.TTF",
            "C:/Windows/Fonts/STHEI.TTF",
            "C:/Windows/Fonts/STKAITI.TTF",
            # Linux 字体路径
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    self._font_registered = True
                    return
                except Exception:
                    continue
        
        # 如果没有找到中文字体，使用内置字体
        self._font_registered = False
    
    def _draw_paper_content(self, paper: Dict[str, Any]):
        """绘制试卷内容"""
        self.config._current_page = 1
        
        page_width, page_height = self.config.get_page_size_tuple()
        
        # 绘制标题
        title = paper.get("title", "无标题")
        y_position = page_height - self.config.margin_top - self.config.title_font_size
        
        self._canvas.setFont("Helvetica-Bold", self.config.title_font_size)
        self._canvas.drawCentredString(
            page_width / 2,
            y_position,
            title
        )
        
        # 绘制试卷信息
        y_position -= self.config.body_font_size * 2
        self._canvas.setFont("Helvetica", self.config.body_font_size)
        
        info_texts = []
        if paper.get("subject"):
            info_texts.append(f"科目：{paper['subject']}")
        if paper.get("total_score"):
            info_texts.append(f"总分：{paper['total_score']}分")
        if paper.get("duration"):
            info_texts.append(f"时长：{paper['duration']}分钟")
        
        for i, text in enumerate(info_texts):
            self._canvas.drawString(
                self.config.margin_left,
                y_position - i * self.config.body_font_size * 1.5,
                text
            )
        
        y_position -= len(info_texts) * self.config.body_font_size * 2
        
        # 绘制题目
        questions = paper.get("questions", [])
        current_section = ""
        
        for idx, question in enumerate(questions, 1):
            q_type = question.get("type", "")
            content = question.get("content", "")
            score = question.get("score", 0)
            
            # 绘制大题标题
            if q_type in self.QUESTION_PREFIXES:
                section = self.QUESTION_PREFIXES[q_type]
                if section != current_section:
                    y_position -= self.config.body_font_size * 2
                    self._canvas.setFont("Helvetica-Bold", self.config.body_font_size + 2)
                    self._canvas.drawString(
                        self.config.margin_left,
                        y_position,
                        section
                    )
                    current_section = section
                    y_position -= self.config.body_font_size * 2
            
            # 绘制题号和内容
            self._canvas.setFont("Helvetica", self.config.body_font_size)
            
            # 题号
            question_text = f"{idx}. {content}"
            
            # 分值
            if self.config.include_scores:
                question_text += f"（{score}分）"
            
            # 绘制文本（自动换行）
            y_position = self._draw_wrapped_text(
                question_text,
                self.config.margin_left + 20,
                y_position,
                self.config._content_width - 20
            )
            
            # 绘制选项
            if "options" in question:
                y_position -= self.config.body_font_size * 0.5
                for opt in question["options"]:
                    opt_text = f"    {opt['key']}. {opt['content']}"
                    y_position = self._draw_wrapped_text(
                        opt_text,
                        self.config.margin_left + 30,
                        y_position,
                        self.config._content_width - 30
                    )
            
            # 绘制答案
            if self.config.include_answers and question.get("answer"):
                y_position -= self.config.body_font_size * 0.5
                answer_text = f"答案：{question['answer']}"
                self._canvas.setFont("Helvetica-Oblique", self.config.body_font_size)
                self._canvas.setFillColorRGB(0.2, 0.2, 0.6)
                y_position = self._draw_wrapped_text(
                    answer_text,
                    self.config.margin_left + 30,
                    y_position,
                    self.config._content_width - 30
                )
                self._canvas.setFillColorRGB(0, 0, 0)
            
            # 题目间隔
            y_position -= self.config.body_font_size * 2
            
            # 检查是否需要分页
            if y_position < self.config.margin_bottom + self.config.body_font_size:
                self._canvas.showPage()
                self.config._current_page += 1
                y_position = page_height - self.config.margin_top
    
    def _draw_wrapped_text(
        self, 
        text: str, 
        x: float, 
        y: float, 
        max_width: float
    ) -> float:
        """
        绘制自动换行的文本
        
        Returns:
            float: 绘制后的 y 位置
        """
        # 简单换行处理（按空格分割）
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            # 估算宽度（简化处理）
            if len(test_line) * self.config.body_font_size * 0.5 < max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # 绘制每行
        line_height = self.config.body_font_size * self.config.line_spacing
        for i, line in enumerate(lines):
            self._canvas.drawString(x, y - i * line_height, line)
        
        return y - len(lines) * line_height
    
    def _draw_answer_sheet(self, paper: Dict[str, Any]):
        """绘制答题卡"""
        self._canvas.showPage()
        self.config._current_page += 1
        
        page_width, page_height = self.config.get_page_size_tuple()
        y_position = page_height - self.config.margin_top
        
        # 标题
        self._canvas.setFont("Helvetica-Bold", self.config.title_font_size)
        self._canvas.drawCentredString(
            page_width / 2,
            y_position,
            "答题卡"
        )
        
        self._draw_answer_sheet_content(self._canvas, paper)
    
    def _draw_answer_sheet_content(self, canvas, paper: Dict[str, Any]):
        """绘制答题卡内容"""
        page_width, page_height = self.config.get_page_size_tuple()
        y_position = page_height - self.config.margin_top - self.config.title_font_size * 2
        
        self._canvas.setFont("Helvetica", self.config.body_font_size)
        
        questions = paper.get("questions", [])
        option_types = ["single", "multiple"]  # 需要答题卡的题型
        
        col_count = 0
        for question in questions:
            if question.get("type") in option_types:
                col_count += 1
        
        # 绘制答题表格
        # 简化处理：绘制选项列表
        y_position -= self.config.body_font_size * 2
        
        self._canvas.drawString(
            self.config.margin_left,
            y_position,
            f"考生答题处（选择题答案）:"
        )
        
        y_position -= self.config.body_font_size * 2
        
        # 绘制选项区域
        row = 0
        col = 0
        options_per_row = 5
        
        for idx, question in enumerate(questions, 1):
            if question.get("type") in option_types:
                x = self.config.margin_left + col * 60
                self._canvas.drawString(x, y_position, f"{idx}.")
                self._canvas.rect(x + 20, y_position - 2, 40, 15)
                
                col += 1
                if col >= options_per_row:
                    col = 0
                    row += 1
                    y_position -= self.config.body_font_size * 2
    
    def generate_filename(self, paper: Dict[str, Any], format: str = "pdf") -> str:
        """生成文件名"""
        title = paper.get("title", "试卷")
        subject = paper.get("subject", "unknown")
        
        # 清理文件名
        title = title.replace(" ", "_").replace("/", "_").replace("\\", "_")
        
        return f"{subject}_{title}.{format}"
    
    def get_page_count(self, paper: Dict[str, Any]) -> int:
        """估算页数"""
        questions = paper.get("questions", [])
        questions_per_page = 5  # 估算值
        
        base_pages = 1  # 标题页
        question_pages = (len(questions) + questions_per_page - 1) // questions_per_page
        
        total = base_pages + question_pages
        
        if self.config.include_answer_sheet:
            total += 1
        
        return total


# ============================================================================
# 便捷函数
# ============================================================================

def export_paper_to_pdf(
    paper: Dict[str, Any],
    config: Optional[PDFExportConfig] = None,
    output_path: Optional[str] = None
) -> BytesIO:
    """
    导出试卷为 PDF 的便捷函数
    
    Args:
        paper: 试卷数据
        config: 导出配置（可选）
        output_path: 输出路径（可选）
        
    Returns:
        BytesIO: PDF 文件缓冲区
    """
    service = PDFExportService(config)
    return service.export_paper(paper, output_path)


def export_paper_and_answer_sheet(
    paper: Dict[str, Any],
    config: Optional[PDFExportConfig] = None
) -> Tuple[BytesIO, BytesIO]:
    """
    分离导出试卷和答题卡
    
    Args:
        paper: 试卷数据
        config: 导出配置（可选）
        
    Returns:
        Tuple[BytesIO, BytesIO]: (试卷PDF, 答题卡PDF)
    """
    service = PDFExportService(config)
    return service.export_separate(paper)


# ============================================================================
# 主入口
# ============================================================================

if __name__ == "__main__":
    # 测试代码
    config = PDFExportConfig(
        include_answers=True,
        include_scores=True,
        page_size="A4"
    )
    
    sample_paper = {
        "id": 1,
        "title": "高一数学期中考试试卷",
        "subject": "math",
        "total_score": 150,
        "duration": 120,
        "questions": [
            {
                "id": 1,
                "type": "single",
                "content": "已知集合A={1,2,3}, B={2,3,4}, 则A∩B等于？",
                "options": [
                    {"key": "A", "content": "{1,2}"},
                    {"key": "B", "content": "{2,3}"},
                    {"key": "C", "content": "{3,4}"},
                    {"key": "D", "content": "{1,4}"}
                ],
                "answer": "B",
                "score": 5
            }
        ]
    }
    
    print("PDF Export Service initialized successfully!")
    print(f"Config: {config}")
