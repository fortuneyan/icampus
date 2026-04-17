"""
Knowledge Base Model - 知识库数据模型

用于存储知识库的元数据
"""

from sqlalchemy import Column, String, Text, Integer, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.timestamp import TimestampMixin


class KnowledgeBaseModel(Base, TimestampMixin):
    """知识库模型"""

    __tablename__ = "ai_knowledge_bases"

    id = Column(String(12), primary_key=True, comment="知识库ID")
    name = Column(String(200), nullable=False, comment="知识库名称")
    description = Column(Text, nullable=True, comment="描述")
    document_count = Column(Integer, default=0, comment="文档数量")
    status = Column(String(20), default="active", comment="状态")
    embedding_model = Column(String(100), nullable=True, comment="嵌入模型")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "document_count": self.document_count,
            "status": self.status,
            "embedding_model": self.embedding_model,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class KnowledgeDocumentModel(Base, TimestampMixin):
    """知识文档模型"""

    __tablename__ = "ai_knowledge_documents"

    id = Column(String(12), primary_key=True, comment="文档ID")
    knowledge_base_id = Column(
        String(12), nullable=False, index=True, comment="知识库ID"
    )
    filename = Column(String(500), nullable=False, comment="文件名")
    file_path = Column(String(1000), nullable=True, comment="文件路径")
    file_type = Column(String(20), nullable=True, comment="文件类型")
    section_count = Column(Integer, default=0, comment="段落数")
    status = Column(String(20), default="pending", comment="处理状态")
    error_message = Column(Text, nullable=True, comment="错误信息")

    def to_dict(self):
        return {
            "id": self.id,
            "knowledge_base_id": self.knowledge_base_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "section_count": self.section_count,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
