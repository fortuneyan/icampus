"""
资产管理Schema
"""

from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field


class AssetCategoryBase(BaseModel):
    """资产分类基础Schema"""
    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=50)
    parent_id: Optional[UUID] = Field(default=None)
    depreciation_years: Optional[int] = Field(default=None, ge=1, le=100)


class AssetCategoryCreate(AssetCategoryBase):
    """创建分类Schema"""
    pass


class AssetCategoryUpdate(BaseModel):
    """更新分类Schema"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    code: Optional[str] = Field(default=None, min_length=1, max_length=50)
    parent_id: Optional[UUID] = None
    depreciation_years: Optional[int] = None


class AssetCategoryRead(AssetCategoryBase):
    """分类读取Schema"""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class AssetBase(BaseModel):
    """资产基础Schema"""
    asset_no: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    category_id: UUID
    model: Optional[str] = Field(default=None, max_length=100)
    brand: Optional[str] = Field(default=None, max_length=50)
    specs: Optional[dict] = Field(default=None)
    location: str = Field(..., max_length=200)
    purchase_date: Optional[date] = None
    purchase_price: Optional[float] = Field(default=None, ge=0)
    supplier: Optional[str] = Field(default=None, max_length=100)
    warranty_period: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = Field(default=None, max_length=500)


class AssetCreate(AssetBase):
    """创建资产Schema"""
    pass


class AssetUpdate(BaseModel):
    """更新资产Schema"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    model: Optional[str] = Field(default=None, max_length=100)
    brand: Optional[str] = Field(default=None, max_length=50)
    specs: Optional[dict] = None
    location: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=500)


class AssetRead(AssetBase):
    """资产读取Schema"""
    id: UUID
    category_name: Optional[str] = None
    status: str = Field(description="状态: idle/in_use/repairing/scrapped")
    custodian_id: Optional[UUID] = None
    custodian_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetListItem(BaseModel):
    """资产列表项Schema"""
    id: UUID
    asset_no: str
    name: str
    category_name: Optional[str] = None
    model: Optional[str] = None
    status: str
    location: str
    custodian_name: Optional[str] = None
    purchase_date: Optional[date] = None

    class Config:
        from_attributes = True


class AssetOperationBase(BaseModel):
    """资产操作基础Schema"""
    operation_type: str = Field(..., description="操作类型: claim/return/transfer/repair/scrap")
    remark: Optional[str] = Field(default=None, max_length=500)


class AssetOperationCreate(AssetOperationBase):
    """创建操作记录Schema"""
    target_user_id: Optional[UUID] = None


class AssetOperationRead(AssetOperationBase):
    """操作记录读取Schema"""
    id: UUID
    asset_id: UUID
    operator_id: UUID
    operator_name: Optional[str] = None
    target_user_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AssetImportItem(BaseModel):
    """导入项Schema"""
    asset_no: str
    name: str
    category_code: str
    model: Optional[str] = None
    location: str
    purchase_date: Optional[str] = None
    purchase_price: Optional[float] = None


class AssetImportResult(BaseModel):
    """导入结果Schema"""
    success_count: int
    fail_count: int
    errors: List[dict]
