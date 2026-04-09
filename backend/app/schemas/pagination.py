"""
分页相关 Schemas
"""

from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    """分页参数"""

    page: int = Field(default=1, ge=1, description="当前页")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")


class PageResult(BaseModel, Generic[T]):
    """分页结果"""

    items: List[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总条数")
    page: int = Field(default=1, description="当前页")
    page_size: int = Field(default=20, description="每页条数")
    total_pages: int = Field(default=0, description="总页数")


class PageResponse(BaseModel):
    """分页响应"""

    code: int = 200
    message: str = "success"
    data: Optional[PageResult] = None


class ListParams(BaseModel):
    """列表查询参数"""

    keyword: Optional[str] = Field(None, description="关键词搜索")
    status: Optional[str] = Field(None, description="状态筛选")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", description="排序方向: asc/desc")


class DeleteParams(BaseModel):
    """删除参数"""

    ids: List[str] = Field(..., description="ID列表")


class BatchOperation(BaseModel):
    """批量操作"""

    ids: List[str] = Field(..., description="ID列表")
    operation: str = Field(..., description="操作类型: enable/disable/delete")
