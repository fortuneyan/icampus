"""
时间戳混入

为模型自动添加 created_at 和 updated_at 字段
"""
from datetime import datetime
from sqlalchemy import Column, DateTime


class TimestampMixin:
    """时间戳混入，自动添加创建时间和更新时间"""

    created_at = Column(
        DateTime,
        default=datetime.now,
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
        comment="更新时间"
    )
