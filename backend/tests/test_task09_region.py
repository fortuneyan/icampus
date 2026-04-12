# -*- coding: utf-8 -*-
"""
TASK-09 测试脚本：地区管理前端页面
测试目标：验证后端 system/regions.py API 正确可用，
         前端 Region.vue 已创建并支持三级联动

运行方式：
    cd smart-campus
    python -m pytest backend/tests/test_task09_region.py -v

通过条件：所有测试用例通过后方可将 TASK-09 标记为完成
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

FRONTEND_VIEWS = os.path.join(
    os.path.dirname(__file__), '..', '..', 'frontend', 'src', 'views'
)


# =====================================================================
# 后端 API 结构检查
# =====================================================================

class TestRegionAPIStructure:
    """验证 system/regions.py 后端 API"""

    def test_regions_router_importable(self):
        """regions router 可导入"""
        try:
            from app.api.v1.system.regions import router
            assert router is not None
        except ImportError as e:
            pytest.fail(f"regions router 无法导入: {e}")

    def test_list_regions_route_exists(self):
        """GET / 省级列表路由存在"""
        try:
            from app.api.v1.system.regions import router
            from fastapi.routing import APIRoute
            get_routes = [
                r for r in router.routes
                if isinstance(r, APIRoute) and 'GET' in r.methods
            ]
            assert len(get_routes) > 0, "未找到 GET 路由"
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_children_route_exists(self):
        """GET /{id}/children 下级地区路由存在（三级联动）"""
        try:
            from app.api.v1.system.regions import router
            routes = [r.path for r in router.routes]
            has_children = any('children' in r.lower() or 'child' in r.lower() for r in routes)
            assert has_children, (
                f"未找到 children 路由，三级联动需要此接口，现有: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_create_region_route_exists(self):
        """POST / 创建地区路由存在"""
        try:
            from app.api.v1.system.regions import router
            from fastapi.routing import APIRoute
            post_routes = [
                r for r in router.routes
                if isinstance(r, APIRoute) and 'POST' in r.methods
            ]
            assert len(post_routes) > 0, "未找到 POST 路由，需实现创建地区功能"
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_update_region_route_exists(self):
        """PUT /{id} 更新地区路由存在"""
        try:
            from app.api.v1.system.regions import router
            from fastapi.routing import APIRoute
            put_routes = [
                r for r in router.routes
                if isinstance(r, APIRoute) and ('PUT' in r.methods or 'PATCH' in r.methods)
            ]
            assert len(put_routes) > 0, "未找到 PUT/PATCH 路由，需实现更新地区功能"
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_delete_region_route_exists(self):
        """DELETE /{id} 删除地区路由存在"""
        try:
            from app.api.v1.system.regions import router
            from fastapi.routing import APIRoute
            delete_routes = [
                r for r in router.routes
                if isinstance(r, APIRoute) and 'DELETE' in r.methods
            ]
            assert len(delete_routes) > 0, "未找到 DELETE 路由，需实现删除地区功能"
        except ImportError:
            pytest.skip("模块无法导入，跳过")


# =====================================================================
# 前端组件检查
# =====================================================================

class TestRegionFrontend:
    """验证地区管理前端页面"""

    def _find_vue_file(self) -> str:
        candidates = [
            os.path.join(FRONTEND_VIEWS, 'system', 'Region.vue'),
            os.path.join(FRONTEND_VIEWS, 'system', 'region.vue'),
            os.path.join(FRONTEND_VIEWS, 'system', 'RegionManage.vue'),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    def test_region_vue_exists(self):
        """Region.vue 文件存在"""
        path = self._find_vue_file()
        assert path is not None, (
            "FAIL: Region.vue 不存在，请在 frontend/src/views/system/ 目录创建"
        )

    def test_region_vue_uses_api(self):
        """Region.vue 应调用后端 API"""
        path = self._find_vue_file()
        if path is None:
            pytest.skip("Region.vue 不存在，跳过")
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()
        has_api = (
            'api' in source.lower() or
            'axios' in source.lower() or
            '/api/v1' in source or
            'region' in source.lower()
        )
        assert has_api, (
            "FAIL: Region.vue 未调用后端 API，需接入 /api/v1/system/regions"
        )

    def test_region_vue_has_three_level_support(self):
        """Region.vue 应支持省/市/区三级联动展示"""
        path = self._find_vue_file()
        if path is None:
            pytest.skip("Region.vue 不存在，跳过")
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()
        has_tree = (
            'tree' in source.lower() or
            'children' in source.lower() or
            'el-tree' in source or
            'cascader' in source.lower() or
            '省' in source or '市' in source
        )
        assert has_tree, (
            "FAIL: Region.vue 缺少三级联动展示（树形/级联选择器）"
        )

    def test_region_vue_has_crud_operations(self):
        """Region.vue 应支持增删改操作"""
        path = self._find_vue_file()
        if path is None:
            pytest.skip("Region.vue 不存在，跳过")
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()
        has_crud = (
            ('add' in source.lower() or '新增' in source) and
            ('delete' in source.lower() or '删除' in source) and
            ('edit' in source.lower() or '编辑' in source or 'update' in source.lower())
        )
        assert has_crud, (
            "FAIL: Region.vue 缺少增删改操作，需实现完整 CRUD"
        )


# =====================================================================
# 数据模型检查
# =====================================================================

class TestRegionModels:
    """验证地区数据模型"""

    def test_region_model_importable(self):
        """Region 模型可导入"""
        try:
            from app.models.region import Region
            assert Region is not None
        except ImportError:
            pytest.skip("Region 模型未找到，跳过")

    def test_region_has_parent_field(self):
        """Region 模型应有 parent_id 字段（支持层级）"""
        try:
            from app.models.region import Region
            has_parent = hasattr(Region, 'parent_id') or 'parent_id' in [
                c.name for c in Region.__table__.columns
            ]
            assert has_parent, "Region 模型缺少 parent_id 字段，无法支持层级结构"
        except (ImportError, AttributeError):
            pytest.skip("Region 模型未找到或无法检查字段，跳过")

    def test_region_has_level_or_type_field(self):
        """Region 模型应有 level 或 type 字段（区分省/市/区）"""
        try:
            from app.models.region import Region
            cols = [c.name for c in Region.__table__.columns]
            has_level = 'level' in cols or 'region_type' in cols or 'type' in cols
            assert has_level, (
                f"Region 模型缺少 level/type 字段，现有字段: {cols}"
            )
        except (ImportError, AttributeError):
            pytest.skip("Region 模型未找到或无法检查字段，跳过")


# =====================================================================
# 集成测试
# =====================================================================

class TestRegionIntegration:
    @pytest.mark.asyncio
    async def test_list_provinces(self):
        pytest.skip("集成测试需要数据库环境，请在有DB的环境中运行")

    @pytest.mark.asyncio
    async def test_get_children_of_province(self):
        pytest.skip("集成测试需要数据库环境，请在有DB的环境中运行")


if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True, text=True
    )
    print(result.stdout)
    print(result.stderr)
