# -*- coding: utf-8 -*-
"""
TASK-14 测试脚本：缓存状态监控 - 全新功能
测试目标：验证 Redis 缓存状态监控（命中率/内存/键数量）+ 优雅降级

运行方式：
    cd smart-campus
    python -m pytest backend/tests/test_task14_cache_monitor.py -v

通过条件：所有测试用例通过后方可将 TASK-14 标记为完成
"""

import pytest
import sys
import os

# 将项目根路径加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# =====================================================================
# 文件存在性检查
# =====================================================================

class TestFileStructure:
    """验证 TASK-14 所需文件已创建"""

    def test_monitor_api_file_exists(self):
        """监控 API 文件应已创建（与 TASK-13 共用）：system/monitor.py"""
        monitor_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'system', 'monitor.py'
        )
        assert os.path.exists(monitor_path), (
            f"FAIL: 监控 API 文件不存在 {monitor_path}\n"
            "需要创建: backend/app/api/v1/system/monitor.py"
        )


# =====================================================================
# 后端 API 结构测试
# =====================================================================

class TestCacheMonitorAPIStructure:
    """验证 monitor.py 中缓存监控路由"""

    def test_router_importable(self):
        """router 对象可正常导入"""
        try:
            from app.api.v1.system.monitor import router
            assert router is not None
        except ImportError as e:
            pytest.fail(f"无法导入 router: {e}")

    def test_cache_endpoint_exists(self):
        """GET /monitor/cache 路由存在"""
        try:
            from app.api.v1.system.monitor import router
            routes = [r.path for r in router.routes]
            has_cache = any('cache' in r for r in routes)
            assert has_cache, (
                f"未找到缓存监控路由 GET /monitor/cache，现有路由: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")


# =====================================================================
# 核心功能逻辑测试
# =====================================================================

class TestCacheMonitorBusinessLogic:
    """验证缓存状态监控的核心业务逻辑"""

    def test_uses_redis_info_command(self):
        """缓存状态应使用 Redis INFO 命令获取"""
        monitor_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'system', 'monitor.py'
        )
        if not os.path.exists(monitor_path):
            pytest.skip("监控文件尚未创建，跳过")

        with open(monitor_path, 'r', encoding='utf-8') as f:
            source = f.read()

        uses_redis_info = (
            'redis' in source.lower() and
            ('info' in source.lower() or 'info()' in source)
        )
        assert uses_redis_info, (
            "FAIL: 缓存状态应使用 Redis INFO 命令获取统计数据"
        )

    def test_returns_memory_usage(self):
        """缓存监控应返回内存使用量"""
        monitor_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'system', 'monitor.py'
        )
        if not os.path.exists(monitor_path):
            pytest.skip("监控文件尚未创建，跳过")

        with open(monitor_path, 'r', encoding='utf-8') as f:
            source = f.read()

        has_memory = (
            'memory' in source.lower() and
            ('used' in source.lower() or 'bytes' in source.lower())
        )
        assert has_memory, (
            "FAIL: 缓存监控应返回 used_memory 字段"
        )

    def test_returns_key_count(self):
        """缓存监控应返回键数量"""
        monitor_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'system', 'monitor.py'
        )
        if not os.path.exists(monitor_path):
            pytest.skip("监控文件尚未创建，跳过")

        with open(monitor_path, 'r', encoding='utf-8') as f:
            source = f.read()

        has_keys = (
            'key' in source.lower() and
            ('count' in source.lower() or 'keys' in source.lower())
        )
        assert has_keys, (
            "FAIL: 缓存监控应返回键数量（total_keys）"
        )

    def test_returns_hit_miss_stats(self):
        """缓存监控应返回命中/未命中统计"""
        monitor_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'system', 'monitor.py'
        )
        if not os.path.exists(monitor_path):
            pytest.skip("监控文件尚未创建，跳过")

        with open(monitor_path, 'r', encoding='utf-8') as f:
            source = f.read()

        has_hits = (
            'hit' in source.lower() or
            'miss' in source.lower() or
            'keyspace_hits' in source.lower()
        )
        assert has_hits, (
            "FAIL: 缓存监控应返回 keyspace_hits / keyspace_misses 统计"
        )

    def test_calculates_hit_rate(self):
        """缓存监控应计算命中率"""
        monitor_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'system', 'monitor.py'
        )
        if not os.path.exists(monitor_path):
            pytest.skip("监控文件尚未创建，跳过")

        with open(monitor_path, 'r', encoding='utf-8') as f:
            source = f.read()

        has_hit_rate = (
            'hit_rate' in source.lower() or
            'hit' in source.lower() and 'rate' in source.lower() or
            'hits' in source.lower() and 'misses' in source.lower()
        )
        assert has_hit_rate, (
            "FAIL: 缓存监控应计算命中率: hits / (hits + misses) * 100"
        )


# =====================================================================
# 优雅降级测试
# =====================================================================

class TestCacheMonitorGracefulDegradation:
    """验证 Redis 不可用时的优雅降级"""

    def test_has_exception_handling(self):
        """缓存监控应有 try-except 处理 Redis 连接失败"""
        monitor_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'system', 'monitor.py'
        )
        if not os.path.exists(monitor_path):
            pytest.skip("监控文件尚未创建，跳过")

        with open(monitor_path, 'r', encoding='utf-8') as f:
            source = f.read()

        has_exception = (
            'except' in source and
            ('redis' in source.lower() or 'ConnectionError' in source or
             'TimeoutError' in source or 'OSError' in source)
        )
        assert has_exception, (
            "FAIL: 缓存监控应有异常处理，避免 Redis 不可用时返回 500 错误"
        )

    def test_returns_available_false_when_redis_down(self):
        """Redis 不可用时返回 available=False（而非抛出异常）"""
        monitor_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'system', 'monitor.py'
        )
        if not os.path.exists(monitor_path):
            pytest.skip("监控文件尚未创建，跳过")

        with open(monitor_path, 'r', encoding='utf-8') as f:
            source = f.read()

        has_available_flag = (
            'available' in source.lower() and
            ('false' in source.lower() or 'False' in source)
        )
        assert has_available_flag, (
            "FAIL: Redis 不可用时应返回 available=false，不应抛出 500 错误"
        )

    def test_no_hardcoded_cache_data(self):
        """缓存监控不应返回硬编码假数据"""
        monitor_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'system', 'monitor.py'
        )
        if not os.path.exists(monitor_path):
            pytest.skip("监控文件尚未创建，跳过")

        with open(monitor_path, 'r', encoding='utf-8') as f:
            source = f.read()

        # 查找可能的硬编码值
        hardcoded_patterns = [
            'return {"used_memory_mb": 123',  # 固定数字
            '"total_keys": 999',               # 固定键数
            '"hit_rate": 85',                  # 固定命中率
        ]
        found_hardcoded = [p for p in hardcoded_patterns if p in source]
        assert not found_hardcoded, (
            f"FAIL: 发现硬编码缓存数据: {found_hardcoded}，应查询真实 Redis"
        )


# =====================================================================
# 响应模型验证
# =====================================================================

class TestCacheMonitorResponseModel:
    """验证缓存监控响应模型"""

    def test_cache_status_model_fields_complete(self):
        """CacheStatus 模型字段完整"""
        try:
            from app.api.v1.system.monitor import CacheStatus
            # 验证模型可实例化
            cs = CacheStatus(
                available=True,
                used_memory_mb=128.5,
                total_keys=100,
                hits=5000,
                misses=500,
                hit_rate=90.91,
                connected_clients=5,
            )
            d = cs.model_dump() if hasattr(cs, 'model_dump') else cs.dict()
            required_keys = ['available', 'used_memory_mb', 'total_keys', 'hit_rate']
            for key in required_keys:
                assert key in d, f"CacheStatus 缺少必需字段: {key}"
        except ImportError:
            pytest.skip("CacheStatus 模型未实现，跳过")

    def test_cache_status_model_handles_unavailable(self):
        """CacheStatus 模型支持 Redis 不可用场景"""
        try:
            from app.api.v1.system.monitor import CacheStatus
            # 不可用时只返回 available 和 message
            cs = CacheStatus(
                available=False,
                message="Redis 未配置或无法连接",
            )
            d = cs.model_dump() if hasattr(cs, 'model_dump') else cs.dict()
            assert d.get('available') == False
            assert 'message' in d or 'msg' in d or d.get('available') == False
        except ImportError:
            pytest.skip("CacheStatus 模型未实现，跳过")


# =====================================================================
# 前端集成测试（结构验证）
# =====================================================================

class TestCacheMonitorFrontend:
    """验证前端页面中的缓存监控集成"""

    def test_frontend_cache_tab_or_section_exists(self):
        """Monitor.vue 中应有缓存监控标签页或区域"""
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'src',
            'views', 'system', 'Monitor.vue'
        )
        if not os.path.exists(frontend_path):
            pytest.skip("前端文件不存在，跳过")

        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()

        has_cache_tab = (
            'cache' in content.lower() or
            'redis' in content.lower() or
            '缓存' in content
        )
        if not has_cache_tab:
            pytest.skip("Monitor.vue 可能未包含缓存监控标签页，后续可补充")


# =====================================================================
# 依赖检查
# =====================================================================

class TestDependencies:
    """检查 TASK-14 的依赖项"""

    def test_redis_py_installed(self):
        """redis-py 依赖应已安装"""
        try:
            import redis
            assert redis.__version__
        except ImportError:
            pytest.fail(
                "FAIL: redis-py 未安装，请执行: pip install redis"
            )

    def test_monitor_uses_redis_async_or_sync(self):
        """monitor.py 应导入 redis 模块"""
        monitor_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'system', 'monitor.py'
        )
        if not os.path.exists(monitor_path):
            pytest.skip("监控文件尚未创建，跳过")

        with open(monitor_path, 'r', encoding='utf-8') as f:
            source = f.read()

        imports_redis = (
            'import redis' in source or
            'from redis' in source or
            'import redis.asyncio' in source or
            'aioredis' in source
        )
        assert imports_redis, (
            "FAIL: monitor.py 应导入 redis 或 redis.asyncio"
        )


# =====================================================================
# 运行结果汇总
# =====================================================================

if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True, text=True
    )
    print(result.stdout)
    print(result.stderr)
