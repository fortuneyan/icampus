"""
软删除混入

为模型添加 is_deleted 字段和软删除支持
"""
from sqlalchemy import Column, Boolean


class SoftDeleteMixin:
    """软删除混入，添加 is_deleted 字段"""

    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已删除"
    )

    def soft_delete(self):
        """执行软删除"""
        self.is_deleted = True
