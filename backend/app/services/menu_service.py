"""
菜单服务
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Menu
from app.core.exceptions import NotFoundException, ConflictException
from app.services.base_service import BaseService


class MenuService(BaseService[Menu]):
    """菜单服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(Menu, db)

    async def get_by_name(self, name: str) -> Optional[Menu]:
        """根据名称获取菜单"""
        return await self.get_by_field("name", name)

    async def create_menu(self, data: dict) -> Menu:
        """创建菜单"""
        if data.get("parent_id"):
            parent = await self.get(data["parent_id"])
            if not parent:
                raise NotFoundException("父级菜单不存在")

        return await self.create(data)

    async def update_menu(self, menu_id: UUID, data: dict) -> Menu:
        """更新菜单"""
        menu = await self.get(menu_id)
        if not menu:
            raise NotFoundException("菜单不存在")

        return await self.update(menu_id, data)

    async def get_menu_tree(
        self, parent_id: Optional[UUID] = None, enabled: bool = True
    ) -> List[dict]:
        """获取菜单树形结构"""
        filters = []

        if parent_id:
            filters.append(Menu.parent_id == parent_id)
        else:
            filters.append(Menu.parent_id.is_(None))

        if enabled:
            filters.append(Menu.enabled == True)

        menus = await self.get_all(filters)

        tree = []
        for menu in menus:
            children = await self.get_menu_tree(menu.id, enabled)
            tree.append(
                {
                    "id": str(menu.id),
                    "label": menu.title,
                    "value": str(menu.id),
                    "name": menu.name,
                    "title": menu.title,
                    "icon": menu.icon,
                    "path": menu.path,
                    "component": menu.component,
                    "sort_order": menu.sort_order,
                    "visible": menu.visible,
                    "enabled": menu.enabled,
                    "keep_alive": menu.keep_alive,
                    "permission_code": menu.permission_code,
                    "children": children if children else [],
                }
            )

        return tree

    async def get_user_menus(self, user_id: Optional[UUID] = None) -> List[dict]:
        """获取用户菜单（根据角色权限）"""
        return await self.get_menu_tree()

    async def delete_menu(self, menu_id: UUID) -> bool:
        """删除菜单"""
        menu = await self.get(menu_id)
        if not menu:
            raise NotFoundException("菜单不存在")

        children = await self.get_all([Menu.parent_id == menu_id])
        if children:
            raise ConflictException("请先删除子菜单")

        return await self.delete(menu_id) is not None
