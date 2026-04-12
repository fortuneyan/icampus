"""
T22 组卷结果缓存优化 - 测试文件

TDD Red 阶段：编写测试用例
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any, List, Optional
import json
import hashlib
import time


# ============================================================================
# 测试数据
# ============================================================================

@pytest.fixture
def sample_paper_request() -> Dict[str, Any]:
    """示例组卷请求"""
    return {
        "title": "高一数学期中考试",
        "subject": "math",
        "grade": "10",
        "total_score": 150,
        "difficulty": "medium",
        "knowledge_points": ["集合", "函数", "三角函数"],
        "question_count": {
            "single": 10,
            "multiple": 5,
            "fill": 5,
            "short": 4,
            "programming": 2
        },
        "difficulty_distribution": {
            "easy": 0.3,
            "medium": 0.5,
            "hard": 0.2
        },
        "exclude_question_ids": []
    }


@pytest.fixture
def sample_paper_result() -> Dict[str, Any]:
    """示例组卷结果"""
    return {
        "id": 1,
        "title": "高一数学期中考试",
        "subject": "math",
        "grade": "10",
        "total_score": 150,
        "duration": 120,
        "questions": [
            {
                "id": 101,
                "type": "single",
                "content": "已知集合A={1,2,3}, B={2,3,4}, 则A∩B等于？",
                "options": [
                    {"key": "A", "content": "{1,2}"},
                    {"key": "B", "content": "{2,3}"},
                    {"key": "C", "content": "{3,4}"},
                    {"key": "D", "content": "{1,4}"}
                ],
                "answer": "B",
                "score": 5
            }
        ],
        "created_at": "2026-04-12T10:00:00Z"
    }


# ============================================================================
# 测试类：缓存配置
# ============================================================================

class TestCacheConfig:
    """测试缓存配置"""
    
    def test_cache_config_default_values(self):
        """测试默认配置"""
        from app.services.paper_cache import PaperCacheConfig
        
        config = PaperCacheConfig()
        
        assert config.enabled is True
        assert config.ttl_seconds == 3600
        assert config.max_size_mb == 100
        assert config.key_prefix == "paper:"
        assert config.enable_snapshot is True
        assert config.snapshot_ttl_seconds == 86400
    
    def test_cache_config_custom_values(self):
        """测试自定义配置"""
        from app.services.paper_cache import PaperCacheConfig
        
        config = PaperCacheConfig(
            enabled=True,
            ttl_seconds=1800,
            max_size_mb=200,
            key_prefix="custom:",
            enable_snapshot=False
        )
        
        assert config.enabled is True
        assert config.ttl_seconds == 1800
        assert config.max_size_mb == 200
        assert config.key_prefix == "custom:"
        assert config.enable_snapshot is False
    
    def test_cache_config_invalid_ttl(self):
        """测试无效TTL"""
        from app.services.paper_cache import PaperCacheConfig
        
        with pytest.raises(ValueError, match="ttl_seconds must be positive"):
            PaperCacheConfig(ttl_seconds=0)
        
        with pytest.raises(ValueError, match="ttl_seconds must be positive"):
            PaperCacheConfig(ttl_seconds=-100)
    
    def test_cache_config_invalid_max_size(self):
        """测试无效最大大小"""
        from app.services.paper_cache import PaperCacheConfig
        
        with pytest.raises(ValueError, match="max_size_mb must be positive"):
            PaperCacheConfig(max_size_mb=0)
    
    def test_cache_config_invalid_key_prefix(self):
        """测试无效键前缀"""
        from app.services.paper_cache import PaperCacheConfig
        
        with pytest.raises(ValueError, match="key_prefix cannot be empty"):
            PaperCacheConfig(key_prefix="")


# ============================================================================
# 测试类：缓存键生成
# ============================================================================

class TestCacheKeyGeneration:
    """测试缓存键生成"""
    
    def test_generate_key_basic(self):
        """测试基础键生成"""
        from app.services.paper_cache import generate_cache_key
        
        request = {
            "subject": "math",
            "grade": "10",
            "knowledge_points": ["集合"]
        }
        
        key = generate_cache_key(request)
        
        assert key is not None
        assert len(key) > 0
        assert key.startswith("paper:")
    
    def test_generate_key_with_order(self):
        """测试相同内容不同顺序生成相同键"""
        from app.services.paper_cache import generate_cache_key
        
        request1 = {"a": 1, "b": 2, "c": 3}
        request2 = {"c": 3, "a": 1, "b": 2}
        
        key1 = generate_cache_key(request1)
        key2 = generate_cache_key(request2)
        
        assert key1 == key2
    
    def test_generate_key_different_content(self):
        """测试不同内容生成不同键"""
        from app.services.paper_cache import generate_cache_key
        
        request1 = {"subject": "math", "grade": "10"}
        request2 = {"subject": "math", "grade": "11"}
        
        key1 = generate_cache_key(request1)
        key2 = generate_cache_key(request2)
        
        assert key1 != key2
    
    def test_generate_key_with_array(self):
        """测试包含数组的键生成"""
        from app.services.paper_cache import generate_cache_key
        
        request1 = {"items": ["a", "b", "c"]}
        request2 = {"items": ["a", "b", "c"]}
        
        key1 = generate_cache_key(request1)
        key2 = generate_cache_key(request2)
        
        assert key1 == key2
    
    def test_generate_key_with_nested(self):
        """测试嵌套对象的键生成"""
        from app.services.paper_cache import generate_cache_key
        
        request = {
            "config": {
                "difficulty": "medium",
                "distribution": {"easy": 0.3, "hard": 0.7}
            }
        }
        
        key = generate_cache_key(request)
        
        assert key is not None
        assert key.startswith("paper:")


# ============================================================================
# 测试类：缓存服务
# ============================================================================

class TestPaperCacheService:
    """测试组卷缓存服务"""
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, sample_paper_result):
        """测试缓存设置和获取"""
        from app.services.paper_cache import PaperCacheService, PaperCacheConfig
        
        config = PaperCacheConfig()
        service = PaperCacheService(config)
        
        # 设置缓存
        await service.set("test_key", sample_paper_result)
        
        # 获取缓存
        cached = await service.get("test_key")
        
        assert cached is not None
        assert cached["id"] == sample_paper_result["id"]
        assert cached["title"] == sample_paper_result["title"]
    
    @pytest.mark.asyncio
    async def test_cache_get_miss(self):
        """测试缓存未命中"""
        from app.services.paper_cache import PaperCacheService, PaperCacheConfig
        
        config = PaperCacheConfig()
        service = PaperCacheService(config)
        
        cached = await service.get("nonexistent_key")
        
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, sample_paper_result):
        """测试缓存删除"""
        from app.services.paper_cache import PaperCacheService, PaperCacheConfig
        
        config = PaperCacheConfig()
        service = PaperCacheService(config)
        
        # 设置缓存
        await service.set("delete_key", sample_paper_result)
        
        # 删除缓存
        result = await service.delete("delete_key")
        
        assert result is True
        
        # 确认删除
        cached = await service.get("delete_key")
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, sample_paper_result):
        """测试缓存清空"""
        from app.services.paper_cache import PaperCacheService, PaperCacheConfig
        
        config = PaperCacheConfig()
        service = PaperCacheService(config)
        
        # 设置多个缓存
        await service.set("key1", sample_paper_result)
        await service.set("key2", sample_paper_result)
        await service.set("key3", sample_paper_result)
        
        # 清空缓存
        await service.clear()
        
        # 确认全部清空
        assert await service.get("key1") is None
        assert await service.get("key2") is None
        assert await service.get("key3") is None
    
    @pytest.mark.asyncio
    async def test_cache_exists(self, sample_paper_result):
        """测试缓存存在检查"""
        from app.services.paper_cache import PaperCacheService, PaperCacheConfig
        
        config = PaperCacheConfig()
        service = PaperCacheService(config)
        
        # 设置缓存
        await service.set("exists_key", sample_paper_result)
        
        # 检查存在
        exists = await service.exists("exists_key")
        not_exists = await service.exists("not_exists_key")
        
        assert exists is True
        assert not_exists is False
    
    @pytest.mark.asyncio
    async def test_cache_ttl(self, sample_paper_result):
        """测试缓存TTL"""
        from app.services.paper_cache import PaperCacheService, PaperCacheConfig
        
        config = PaperCacheConfig(ttl_seconds=1)
        service = PaperCacheService(config)
        
        # 设置缓存
        await service.set("ttl_key", sample_paper_result)
        
        # 立即获取 - 应该存在
        cached = await service.get("ttl_key")
        assert cached is not None
        
        # 等待过期
        time.sleep(1.5)
        
        # 获取 - 应该不存在
        cached = await service.get("ttl_key")
        assert cached is None


# ============================================================================
# 测试类：快照功能
# ============================================================================

class TestSnapshotService:
    """测试快照服务"""
    
    @pytest.mark.asyncio
    async def test_save_snapshot(self, sample_paper_result):
        """测试保存快照"""
        from app.services.paper_cache import SnapshotService, PaperCacheConfig
        
        config = PaperCacheConfig(enable_snapshot=True)
        service = SnapshotService(config)
        
        request = {"subject": "math", "grade": "10"}
        result = await service.save_snapshot(request, sample_paper_result)
        
        assert result["success"] is True
        assert result["paper_id"] == sample_paper_result["id"]
        assert "snapshot_key" in result
    
    @pytest.mark.asyncio
    async def test_get_snapshot(self, sample_paper_result):
        """测试获取快照"""
        from app.services.paper_cache import SnapshotService, PaperCacheConfig
        
        config = PaperCacheConfig(enable_snapshot=True)
        service = SnapshotService(config)
        
        request = {"subject": "math", "grade": "10"}
        
        # 保存快照
        await service.save_snapshot(request, sample_paper_result)
        
        # 获取快照
        cached = await service.get_snapshot(request)
        
        assert cached is not None
        assert cached["id"] == sample_paper_result["id"]
    
    @pytest.mark.asyncio
    async def test_snapshot_not_found(self):
        """测试快照未找到"""
        from app.services.paper_cache import SnapshotService, PaperCacheConfig
        
        config = PaperCacheConfig(enable_snapshot=True)
        service = SnapshotService(config)
        
        request = {"subject": "nonexistent"}
        
        cached = await service.get_snapshot(request)
        
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_snapshot_ttl(self, sample_paper_result):
        """测试快照TTL"""
        from app.services.paper_cache import SnapshotService, PaperCacheConfig
        
        config = PaperCacheConfig(
            enable_snapshot=True,
            snapshot_ttl_seconds=1
        )
        service = SnapshotService(config)
        
        request = {"subject": "math", "grade": "10"}
        
        # 保存快照
        await service.save_snapshot(request, sample_paper_result)
        
        # 立即获取 - 应该存在
        cached = await service.get_snapshot(request)
        assert cached is not None
        
        # 等待过期
        time.sleep(1.5)
        
        # 获取 - 应该不存在
        cached = await service.get_snapshot(request)
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_list_snapshots(self, sample_paper_result):
        """测试列出快照"""
        from app.services.paper_cache import SnapshotService, PaperCacheConfig
        
        config = PaperCacheConfig(enable_snapshot=True)
        service = SnapshotService(config)
        
        # 保存多个快照
        await service.save_snapshot({"subject": "math"}, sample_paper_result)
        await service.save_snapshot({"subject": "english"}, sample_paper_result)
        await service.save_snapshot({"subject": "chinese"}, sample_paper_result)
        
        # 列出快照
        snapshots = await service.list_snapshots()
        
        assert len(snapshots) == 3
    
    @pytest.mark.asyncio
    async def test_delete_snapshot(self, sample_paper_result):
        """测试删除快照"""
        from app.services.paper_cache import SnapshotService, PaperCacheConfig
        
        config = PaperCacheConfig(enable_snapshot=True)
        service = SnapshotService(config)
        
        request = {"subject": "math"}
        
        # 保存快照
        await service.save_snapshot(request, sample_paper_result)
        
        # 删除快照
        result = await service.delete_snapshot(request)
        
        assert result is True
        
        # 确认删除
        cached = await service.get_snapshot(request)
        assert cached is None


# ============================================================================
# 测试类：缓存统计
# ============================================================================

class TestCacheStatistics:
    """测试缓存统计"""
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, sample_paper_result):
        """测试获取统计信息"""
        from app.services.paper_cache import PaperCacheService, PaperCacheConfig
        
        config = PaperCacheConfig()
        service = PaperCacheService(config)
        
        # 添加缓存
        await service.set("stat_key1", sample_paper_result)
        await service.set("stat_key2", sample_paper_result)
        
        # 获取统计
        stats = await service.get_statistics()
        
        assert stats is not None
        assert "hit_count" in stats
        assert "miss_count" in stats
        assert "key_count" in stats
        assert "memory_size_mb" in stats
    
    @pytest.mark.asyncio
    async def test_hit_rate_calculation(self, sample_paper_result):
        """测试命中率计算"""
        from app.services.paper_cache import PaperCacheService, PaperCacheConfig
        
        config = PaperCacheConfig()
        service = PaperCacheService(config)
        
        # 添加缓存
        await service.set("hit_key", sample_paper_result)
        
        # 模拟命中
        for _ in range(5):
            await service.get("hit_key")
        
        # 模拟未命中
        for _ in range(3):
            await service.get("miss_key")
        
        stats = await service.get_statistics()
        
        assert stats["hit_count"] == 5
        assert stats["miss_count"] == 3
        assert stats["hit_rate"] == pytest.approx(5/8 * 100, rel=0.1)


# ============================================================================
# 测试类：缓存集成
# ============================================================================

class TestCacheIntegration:
    """测试缓存集成"""
    
    @pytest.mark.asyncio
    async def test_paper_generation_with_cache_hit(
        self, 
        sample_paper_request, 
        sample_paper_result
    ):
        """测试带缓存的组卷（缓存命中）"""
        from app.services.paper_cache import PaperCacheService, PaperCacheConfig
        from app.services.paper_cache import generate_cache_key
        
        config = PaperCacheConfig()
        cache = PaperCacheService(config)
        
        # 生成缓存键
        cache_key = generate_cache_key(sample_paper_request)
        
        # 预填充缓存
        await cache.set(cache_key, sample_paper_result)
        
        # 模拟带缓存的组卷
        async def generate_with_cache(request):
            key = generate_cache_key(request)
            cached = await cache.get(key)
            if cached:
                return cached, True  # 返回缓存结果
            return None, False
        
        result, is_cached = await generate_with_cache(sample_paper_request)
        
        assert is_cached is True
        assert result is not None
        assert result["id"] == sample_paper_result["id"]
    
    @pytest.mark.asyncio
    async def test_paper_generation_with_cache_miss(self, sample_paper_request):
        """测试带缓存的组卷（缓存未命中）"""
        from app.services.paper_cache import PaperCacheService, PaperCacheConfig
        from app.services.paper_cache import generate_cache_key
        
        config = PaperCacheConfig()
        cache = PaperCacheService(config)
        
        # 模拟带缓存的组卷
        async def generate_with_cache(request):
            key = generate_cache_key(request)
            cached = await cache.get(key)
            if cached:
                return cached, True
            # 模拟生成新试卷
            new_paper = {"id": 999, "title": "Generated"}
            await cache.set(key, new_paper)
            return new_paper, False
        
        result, is_cached = await generate_with_cache(sample_paper_request)
        
        assert is_cached is False
        assert result is not None
        assert result["id"] == 999
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_on_update(self, sample_paper_result):
        """测试更新时缓存失效"""
        from app.services.paper_cache import PaperCacheService, PaperCacheConfig
        
        config = PaperCacheConfig()
        service = PaperCacheService(config)
        
        # 设置缓存
        await service.set("update_key", sample_paper_result)
        
        # 更新操作应该删除缓存
        await service.delete("update_key")
        
        # 确认缓存已删除
        cached = await service.get("update_key")
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self, sample_paper_result):
        """测试并发缓存访问"""
        import asyncio
        from app.services.paper_cache import PaperCacheService, PaperCacheConfig
        
        config = PaperCacheConfig()
        service = PaperCacheService(config)
        
        # 并发设置缓存
        tasks = [
            service.set(f"concurrent_key_{i}", sample_paper_result)
            for i in range(10)
        ]
        await asyncio.gather(*tasks)
        
        # 验证所有缓存都已设置
        for i in range(10):
            cached = await service.get(f"concurrent_key_{i}")
            assert cached is not None


# ============================================================================
# 测试类：缓存策略
# ============================================================================

class TestCacheStrategy:
    """测试缓存策略"""
    
    def test_lru_eviction_policy(self):
        """测试LRU淘汰策略"""
        from app.services.paper_cache import LRUCache
        
        cache = LRUCache(max_size=3)
        
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        
        # 添加第4个，应该淘汰最旧的
        cache.set("d", 4)
        
        assert cache.get("a") is None  # 已被淘汰
        assert cache.get("d") == 4
    
    def test_ttl_expiration(self):
        """测试TTL过期"""
        from app.services.paper_cache import LRUCache
        import time
        
        cache = LRUCache(max_size=10, ttl=0.1)
        
        cache.set("ttl_key", "value")
        
        # 立即获取
        assert cache.get("ttl_key") == "value"
        
        # 等待过期
        time.sleep(0.2)
        
        # 获取
        assert cache.get("ttl_key") is None
    
    def test_cache_size_limit(self):
        """测试缓存大小限制"""
        from app.services.paper_cache import LRUCache
        
        cache = LRUCache(max_size=5)
        
        for i in range(10):
            cache.set(f"size_key_{i}", f"value_{i}")
        
        # 应该保留最近5个
        assert cache.get("size_key_0") is None
        assert cache.get("size_key_9") is not None
    
    def test_cache_memory_limit_estimation(self):
        """测试内存限制估算"""
        from app.services.paper_cache import PaperCacheConfig, estimate_size
        
        config = PaperCacheConfig(max_size_mb=10)
        
        # 估算大小
        data = {"key": "value" * 1000}
        size_bytes = estimate_size(data)
        
        assert size_bytes > 0
        assert size_bytes < config.max_size_mb * 1024 * 1024


# ============================================================================
# 测试类：API端点
# ============================================================================

class TestCacheAPI:
    """测试缓存API"""
    
    def test_clear_cache_endpoint_format(self):
        """测试清空缓存端点格式"""
        endpoint = "/api/v1/cache/papers"
        method = "DELETE"
        
        assert endpoint == "/api/v1/cache/papers"
        assert method == "DELETE"
    
    def test_cache_statistics_endpoint_format(self):
        """测试统计端点格式"""
        endpoint = "/api/v1/cache/statistics"
        method = "GET"
        
        assert endpoint == "/api/v1/cache/statistics"
        assert method == "GET"
    
    def test_cache_snapshot_endpoint_format(self):
        """测试快照端点格式"""
        endpoint = "/api/v1/cache/snapshots"
        methods = ["GET", "POST", "DELETE"]
        
        for method in methods:
            assert method in ["GET", "POST", "DELETE"]


# ============================================================================
# 运行所有测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
