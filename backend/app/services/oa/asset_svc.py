"""
资产管理服务
"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, date
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.oa.asset import OaAssetCategory, OaAsset, OaBorrowRecord


class AssetCategoryService:
    """资产分类服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_category_tree(self) -> List[Dict[str, Any]]:
        """获取资产分类树"""
        query = select(OaAssetCategory).order_by(OaAssetCategory.sort_order)
        result = await self.db.execute(query)
        categories = result.scalars().all()

        # 构建树形结构
        tree = []
        category_map = {}

        for cat in categories:
            category_map[str(cat.id)] = {
                "id": str(cat.id),
                "name": cat.name,
                "code": cat.code,
                "parent_id": str(cat.parent_id) if cat.parent_id else None,
                "icon": cat.icon,
                "description": cat.description,
                "sort_order": cat.sort_order,
                "children": [],
            }

        for cat_id, cat_data in category_map.items():
            if cat_data["parent_id"]:
                parent = category_map.get(cat_data["parent_id"])
                if parent:
                    parent["children"].append(cat_data)
            else:
                tree.append(cat_data)

        return tree

    async def create_category(self, data: dict) -> OaAssetCategory:
        """创建分类"""
        category = OaAssetCategory(
            name=data.get("name"),
            code=data.get("code"),
            parent_id=data.get("parent_id"),
            icon=data.get("icon"),
            description=data.get("description"),
            sort_order=data.get("sort_order", 0),
        )
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update_category(self, category_id: UUID, data: dict) -> Optional[OaAssetCategory]:
        """更新分类"""
        query = select(OaAssetCategory).where(OaAssetCategory.id == category_id)
        result = await self.db.execute(query)
        category = result.scalar_one_or_none()

        if not category:
            return None

        for key, value in data.items():
            if hasattr(category, key):
                setattr(category, key, value)

        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete_category(self, category_id: UUID) -> bool:
        """删除分类"""
        query = select(OaAssetCategory).where(OaAssetCategory.id == category_id)
        result = await self.db.execute(query)
        category = result.scalar_one_or_none()

        if not category:
            return False

        # 检查是否有子分类或资产
        child_query = select(func.count()).select_from(OaAssetCategory).where(
            OaAssetCategory.parent_id == category_id
        )
        child_result = await self.db.execute(child_query)
        child_count = child_result.scalar() or 0

        if child_count > 0:
            raise ValueError("该分类下存在子分类，无法删除")

        asset_query = select(func.count()).select_from(OaAsset).where(
            OaAsset.category_id == category_id,
            OaAsset.is_deleted == False,
        )
        asset_result = await self.db.execute(asset_query)
        asset_count = asset_result.scalar() or 0

        if asset_count > 0:
            raise ValueError("该分类下存在资产，无法删除")

        await self.db.delete(category)
        await self.db.commit()
        return True


class AssetService:
    """资产管理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_asset_list(
        self,
        page: int = 1,
        page_size: int = 20,
        category_id: Optional[UUID] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取资产列表"""
        query = select(OaAsset).where(OaAsset.is_deleted == False)

        if category_id:
            query = query.where(OaAsset.category_id == category_id)
        if status:
            query = query.where(OaAsset.status == status)
        if keyword:
            query = query.where(
                or_(
                    OaAsset.name.ilike(f"%{keyword}%"),
                    OaAsset.asset_code.ilike(f"%{keyword}%"),
                    OaAsset.brand.ilike(f"%{keyword}%"),
                )
            )

        # 总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页 + 预加载
        query = (
            query
            .options(selectinload(OaAsset.category))
            .order_by(OaAsset.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        assets = result.scalars().all()

        items = []
        for asset in assets:
            items.append({
                "id": str(asset.id),
                "name": asset.name,
                "asset_code": asset.asset_code,
                "category_id": str(asset.category_id) if asset.category_id else None,
                "category_name": asset.category.name if asset.category else None,
                "brand": asset.brand,
                "model": asset.model,
                "status": asset.status,
                "purchase_date": asset.purchase_date.isoformat() if asset.purchase_date else None,
                "purchase_price": float(asset.purchase_price) if asset.purchase_price else None,
                "storage_location": asset.storage_location,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_asset_detail(self, asset_id: UUID) -> Optional[Dict[str, Any]]:
        """获取资产详情"""
        query = (
            select(OaAsset)
            .where(OaAsset.id == asset_id, OaAsset.is_deleted == False)
            .options(selectinload(OaAsset.category))
        )
        result = await self.db.execute(query)
        asset = result.scalar_one_or_none()

        if not asset:
            return None

        return {
            "id": str(asset.id),
            "name": asset.name,
            "asset_code": asset.asset_code,
            "barcode": asset.barcode,
            "qr_code": asset.qr_code,
            "category_id": str(asset.category_id) if asset.category_id else None,
            "category_name": asset.category.name if asset.category else None,
            "brand": asset.brand,
            "model": asset.model,
            "spec_md": asset.spec_md,
            "description_md": asset.description_md,
            "purchase_date": asset.purchase_date.isoformat() if asset.purchase_date else None,
            "purchase_price": float(asset.purchase_price) if asset.purchase_price else None,
            "supplier": asset.supplier,
            "warranty_expire": asset.warranty_expire.isoformat() if asset.warranty_expire else None,
            "storage_location": asset.storage_location,
            "status": asset.status,
            "image_urls": asset.image_urls,
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
        }

    async def create_asset(self, data: dict) -> OaAsset:
        """创建资产"""
        asset = OaAsset(
            name=data.get("name"),
            asset_code=data.get("asset_code"),
            barcode=data.get("barcode"),
            qr_code=data.get("qr_code"),
            category_id=data.get("category_id"),
            brand=data.get("brand"),
            model=data.get("model"),
            spec_md=data.get("spec_md"),
            description_md=data.get("description_md"),
            purchase_date=data.get("purchase_date"),
            purchase_price=data.get("purchase_price"),
            supplier=data.get("supplier"),
            warranty_expire=data.get("warranty_expire"),
            storage_location=data.get("storage_location"),
            image_urls=data.get("image_urls"),
            status=data.get("status", "IDLE"),
        )
        self.db.add(asset)
        await self.db.commit()
        await self.db.refresh(asset)
        return asset

    async def update_asset(self, asset_id: UUID, data: dict) -> Optional[OaAsset]:
        """更新资产"""
        query = select(OaAsset).where(OaAsset.id == asset_id, OaAsset.is_deleted == False)
        result = await self.db.execute(query)
        asset = result.scalar_one_or_none()

        if not asset:
            return None

        for key, value in data.items():
            if hasattr(asset, key):
                setattr(asset, key, value)

        await self.db.commit()
        await self.db.refresh(asset)
        return asset

    async def delete_asset(self, asset_id: UUID) -> bool:
        """删除资产"""
        query = select(OaAsset).where(OaAsset.id == asset_id, OaAsset.is_deleted == False)
        result = await self.db.execute(query)
        asset = result.scalar_one_or_none()

        if not asset:
            return False

        asset.is_deleted = True
        await self.db.commit()
        return True

    async def transfer_asset(
        self,
        asset_id: UUID,
        target_org_id: UUID,
        operator_id: UUID,
    ) -> Optional[OaAsset]:
        """资产调拨"""
        query = select(OaAsset).where(OaAsset.id == asset_id, OaAsset.is_deleted == False)
        result = await self.db.execute(query)
        asset = result.scalar_one_or_none()

        if not asset:
            return None

        asset.current_org_id = target_org_id
        await self.db.commit()
        await self.db.refresh(asset)
        return asset


class BorrowRecordService:
    """借用记录服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_borrow_list(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        asset_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """获取借用记录列表"""
        query = select(OaBorrowRecord).where(OaBorrowRecord.is_deleted == False)

        if status:
            query = query.where(OaBorrowRecord.status == status)
        if asset_id:
            query = query.where(OaBorrowRecord.asset_id == asset_id)

        # 总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页 + 预加载
        query = (
            query
            .options(selectinload(OaBorrowRecord.asset))
            .options(selectinload(OaBorrowRecord.borrower))
            .order_by(OaBorrowRecord.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        records = result.scalars().all()

        items = []
        for record in records:
            items.append({
                "id": str(record.id),
                "asset_id": str(record.asset_id),
                "asset_name": record.asset.name if record.asset else None,
                "asset_code": record.asset.asset_code if record.asset else None,
                "borrower_id": str(record.borrower_id),
                "borrower_name": record.borrower.name if record.borrower else None,
                "borrow_date": record.borrow_date.isoformat() if record.borrow_date else None,
                "expected_return_date": record.expected_return_date.isoformat() if record.expected_return_date else None,
                "actual_return_date": record.actual_return_date.isoformat() if record.actual_return_date else None,
                "status": record.status,
                "purpose_md": record.purpose_md,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_borrow_detail(self, record_id: UUID) -> Optional[Dict[str, Any]]:
        """获取借用记录详情"""
        query = (
            select(OaBorrowRecord)
            .where(OaBorrowRecord.id == record_id, OaBorrowRecord.is_deleted == False)
            .options(selectinload(OaBorrowRecord.asset))
            .options(selectinload(OaBorrowRecord.borrower))
            .options(selectinload(OaBorrowRecord.approver))
        )
        result = await self.db.execute(query)
        record = result.scalar_one_or_none()

        if not record:
            return None

        return {
            "id": str(record.id),
            "asset_id": str(record.asset_id),
            "asset_name": record.asset.name if record.asset else None,
            "asset_code": record.asset.asset_code if record.asset else None,
            "borrower_id": str(record.borrower_id),
            "borrower_name": record.borrower.name if record.borrower else None,
            "borrow_date": record.borrow_date.isoformat() if record.borrow_date else None,
            "expected_return_date": record.expected_return_date.isoformat() if record.expected_return_date else None,
            "actual_return_date": record.actual_return_date.isoformat() if record.actual_return_date else None,
            "actual_return_condition": record.actual_return_condition,
            "status": record.status,
            "purpose_md": record.purpose_md,
            "approver_id": str(record.approver_id) if record.approver_id else None,
            "approver_name": record.approver.name if record.approver else None,
            "approver_comment": record.approver_comment,
            "approved_at": record.approved_at.isoformat() if record.approved_at else None,
        }

    async def create_borrow(
        self,
        asset_id: UUID,
        data: dict,
        borrower_id: UUID,
    ) -> OaBorrowRecord:
        """创建借用记录"""
        record = OaBorrowRecord(
            asset_id=asset_id,
            borrower_id=borrower_id,
            purpose_md=data.get("purpose_md"),
            borrow_date=data.get("borrow_date", date.today()),
            expected_return_date=data.get("expected_return_date"),
            status="PENDING",
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def return_asset(
        self,
        record_id: UUID,
        condition: Optional[str],
        user_id: UUID,
    ) -> Optional[OaBorrowRecord]:
        """归还资产"""
        query = select(OaBorrowRecord).where(
            OaBorrowRecord.id == record_id,
            OaBorrowRecord.borrower_id == user_id,
            OaBorrowRecord.is_deleted == False,
        )
        result = await self.db.execute(query)
        record = result.scalar_one_or_none()

        if not record:
            return None

        record.status = "RETURNED"
        record.actual_return_date = date.today()
        record.actual_return_condition = condition

        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def get_my_borrows(self, user_id: UUID) -> List[Dict[str, Any]]:
        """获取我的借用记录"""
        query = (
            select(OaBorrowRecord)
            .where(
                OaBorrowRecord.borrower_id == user_id,
                OaBorrowRecord.is_deleted == False,
                OaBorrowRecord.status.in_(["PENDING", "APPROVED", "BORROWED"]),
            )
            .options(selectinload(OaBorrowRecord.asset))
        )
        result = await self.db.execute(query)
        records = result.scalars().all()

        items = []
        for record in records:
            items.append({
                "id": str(record.id),
                "asset_id": str(record.asset_id),
                "asset_name": record.asset.name if record.asset else None,
                "asset_code": record.asset.asset_code if record.asset else None,
                "borrow_date": record.borrow_date.isoformat() if record.borrow_date else None,
                "expected_return_date": record.expected_return_date.isoformat() if record.expected_return_date else None,
                "status": record.status,
            })

        return items

    async def get_overdue_borrows(self, user_id: UUID) -> List[Dict[str, Any]]:
        """获取超期借用记录"""
        today = date.today()
        query = (
            select(OaBorrowRecord)
            .where(
                OaBorrowRecord.borrower_id == user_id,
                OaBorrowRecord.is_deleted == False,
                OaBorrowRecord.status.in_(["APPROVED", "BORROWED"]),
                OaBorrowRecord.expected_return_date < today,
            )
            .options(selectinload(OaBorrowRecord.asset))
        )
        result = await self.db.execute(query)
        records = result.scalars().all()

        items = []
        for record in records:
            days_overdue = (today - record.expected_return_date).days
            items.append({
                "id": str(record.id),
                "asset_id": str(record.asset_id),
                "asset_name": record.asset.name if record.asset else None,
                "asset_code": record.asset.asset_code if record.asset else None,
                "expected_return_date": record.expected_return_date.isoformat() if record.expected_return_date else None,
                "days_overdue": days_overdue,
                "status": record.status,
            })

        return items
