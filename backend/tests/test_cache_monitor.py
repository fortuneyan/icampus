"""
缓存监控 API 测试
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_cache_stats(client: AsyncClient):
    """测试获取缓存统计信息"""
    response = await client.get("/api/v1/system/cache/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    stats = data["data"]
    assert "total_keys" in stats
    assert "hit_rate" in stats
    assert "memory_usage" in stats
    assert "expired_keys" in stats


@pytest.mark.asyncio
async def test_get_cache_keys(client: AsyncClient):
    """测试获取缓存键列表"""
    response = await client.get("/api/v1/system/cache/keys")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_cache_types(client: AsyncClient):
    """测试获取缓存类型分布"""
    response = await client.get("/api/v1/system/cache/types")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    types = data["data"]
    assert isinstance(types, list)


@pytest.mark.asyncio
async def test_get_memory_trend(client: AsyncClient):
    """测试获取内存使用趋势"""
    response = await client.get("/api/v1/system/cache/memory-trend?hours=24")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    trend = data["data"]
    assert "hours" in trend
    assert "data" in trend
    assert "current" in trend


@pytest.mark.asyncio
async def test_clear_expired_keys(client: AsyncClient):
    """测试清理过期缓存键"""
    response = await client.post("/api/v1/system/cache/clear-expired")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    assert "cleared_count" in data["data"]


@pytest.mark.asyncio
async def test_cache_key_operations(client: AsyncClient):
    """测试缓存键操作"""
    # 获取缓存键列表，取第一个进行测试
    list_response = await client.get("/api/v1/system/cache/keys?page_size=1")
    assert list_response.status_code == 200
    list_data = list_response.json()
    
    if list_data["data"] and len(list_data["data"]) > 0:
        key = list_data["data"][0]["key"]
        encoded_key = key.replace(":", "%3A")
        
        # 获取键详情
        get_response = await client.get(f"/api/v1/system/cache/keys/{encoded_key}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["code"] == 200
        
        # 更新TTL
        ttl_response = await client.post(f"/api/v1/system/cache/keys/{encoded_key}/ttl?ttl=3600")
        assert ttl_response.status_code == 200
        ttl_data = ttl_response.json()
        assert ttl_data["code"] == 200
