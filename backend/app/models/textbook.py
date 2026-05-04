# 教材管理数据模型
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, Boolean, Date, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.soft_delete import SoftDeleteMixin
from app.models.timestamp import TimestampMixin
import enum


class TextbookStatus(str, enum.Enum):
    """教材状态枚举"""
    DRAFT = "draft"           # 草稿
    PUBLISHED = "published"   # 已发布
    OUT_OF_STOCK = "out_of_stock"  # 缺货
    DISCONTINUED = "discontinued"  # 停用


class TextbookLevel(str, enum.Enum):
    """教材适用年级枚举"""
    GRADE_1 = "grade_1"       # 一年级
    GRADE_2 = "grade_2"       # 二年级
    GRADE_3 = "grade_3"       # 三年级
    GRADE_4 = "grade_4"       # 四年级
    GRADE_5 = "grade_5"       # 五年级
    GRADE_6 = "grade_6"       # 六年级
    GRADE_7 = "grade_7"       # 七年级（初一）
    GRADE_8 = "grade_8"       # 八年级（初二）
    GRADE_9 = "grade_9"       # 九年级（初三）
    HIGH_1 = "high_1"         # 高一
    HIGH_2 = "high_2"         # 高二
    HIGH_3 = "high_3"         # 高三


class Textbook(Base, TimestampMixin, SoftDeleteMixin):
    """
    教材表

    存储学校使用的教材信息，包括基本信息、库存、适用年级等
    """
    __tablename__ = "edu_textbooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 基本信息
    isbn = Column(String(20), unique=True, index=True, nullable=False, comment="ISBN编号")
    title = Column(String(200), nullable=False, comment="教材名称")
    subtitle = Column(String(200), nullable=True, comment="副标题")
    author = Column(String(100), nullable=True, comment="作者/编者")
    publisher = Column(String(100), nullable=True, comment="出版社")

    # 分类信息
    subject = Column(String(50), nullable=True, index=True, comment="学科")
    grade_level = Column(SQLEnum(TextbookLevel), nullable=True, comment="适用年级")
    semester = Column(String(20), nullable=True, comment="适用学期")
    edition = Column(String(50), nullable=True, comment="版次")

    # 价格和库存
    price = Column(Float, default=0.0, comment="定价")
    cost_price = Column(Float, default=0.0, comment="进价")
    stock_quantity = Column(Integer, default=0, comment="库存数量")
    min_stock = Column(Integer, default=10, comment="最低库存")
    reorder_point = Column(Integer, default=20, comment="补货点")

    # 内容信息
    description = Column(Text, nullable=True, comment="教材简介")
    cover_image = Column(String(500), nullable=True, comment="封面图片URL")
    page_count = Column(Integer, nullable=True, comment="页数")

    # 状态
    status = Column(SQLEnum(TextbookStatus), default=TextbookStatus.DRAFT, comment="状态")

    # 关联关系
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=True, comment="关联课程")
    course = relationship("Course")
    adoptions = relationship("TextbookAdoption", back_populates="textbook", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """设置默认值"""
        # 价格和库存默认值
        if 'price' not in kwargs or kwargs['price'] is None:
            kwargs['price'] = 0.0
        if 'cost_price' not in kwargs or kwargs['cost_price'] is None:
            kwargs['cost_price'] = 0.0
        if 'stock_quantity' not in kwargs or kwargs['stock_quantity'] is None:
            kwargs['stock_quantity'] = 0
        if 'min_stock' not in kwargs or kwargs['min_stock'] is None:
            kwargs['min_stock'] = 10
        if 'reorder_point' not in kwargs or kwargs['reorder_point'] is None:
            kwargs['reorder_point'] = 20
        if 'status' not in kwargs or kwargs['status'] is None:
            kwargs['status'] = TextbookStatus.DRAFT
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": str(self.id),
            "isbn": self.isbn,
            "title": self.title,
            "subtitle": self.subtitle,
            "author": self.author,
            "publisher": self.publisher,
            "subject": self.subject,
            "grade_level": self.grade_level.value if self.grade_level else None,
            "grade_level_text": self.grade_level.value if self.grade_level else None,
            "semester": self.semester,
            "edition": self.edition,
            "price": self.price,
            "cost_price": self.cost_price,
            "stock_quantity": self.stock_quantity,
            "min_stock": self.min_stock,
            "reorder_point": self.reorder_point,
            "description": self.description,
            "cover_image": self.cover_image,
            "page_count": self.page_count,
            "status": self.status.value if self.status else None,
            "status_text": self.status.value if self.status else None,
            "course_id": self.course_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Textbook(id={self.id}, isbn={self.isbn}, title={self.title})>"


class TextbookAdoption(Base, TimestampMixin):
    """
    教材选用记录表

    记录每个班级/年级选用的教材
    """
    __tablename__ = "edu_textbook_adoptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    textbook_id = Column(UUID(as_uuid=True), ForeignKey("edu_textbooks.id"), nullable=False, comment="教材ID")
    grade_level = Column(SQLEnum(TextbookLevel), nullable=False, comment="年级")
    semester = Column(String(20), nullable=False, comment="学期")
    school_year = Column(String(20), nullable=False, comment="学年")

    # 选用信息
    adoption_year = Column(Integer, nullable=True, comment="选用年份")
    adoption_reason = Column(Text, nullable=True, comment="选用理由")
    approved_by = Column(String(100), nullable=True, comment="审批人")
    approved_at = Column(Date, nullable=True, comment="审批时间")
    is_mandatory = Column(Boolean, default=True, comment="是否必修")

    # 关联关系
    textbook = relationship("Textbook", back_populates="adoptions")

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": str(self.id),
            "textbook_id": self.textbook_id,
            "grade_level": self.grade_level.value if self.grade_level else None,
            "semester": self.semester,
            "school_year": self.school_year,
            "adoption_year": self.adoption_year,
            "adoption_reason": self.adoption_reason,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "is_mandatory": self.is_mandatory,
        }

    def __repr__(self):
        return f"<TextbookAdoption(id={self.id}, textbook_id={self.textbook_id}, grade={self.grade_level})>"
