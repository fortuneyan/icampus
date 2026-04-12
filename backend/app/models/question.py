"""
题库管理模块 - 数据模型扩展

本模块从 app.models.exam 导入核心模型，并添加题库专用扩展
"""
from app.models.exam import (
    Question, 
    QuestionAnnotation, 
    ExamPaper, 
    PaperQuestion,
    SimilarityCheckRecord
)

# 导出核心模型供其他模块使用
__all__ = [
    "Question", 
    "QuestionAnnotation", 
    "ExamPaper", 
    "PaperQuestion",
    "SimilarityCheckRecord"
]
