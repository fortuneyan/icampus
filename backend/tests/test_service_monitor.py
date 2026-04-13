"""
服务监控 API 测试
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_system_info(client: AsyncClient):
    """测试获取系统资源信息"""
    response = await client.get("/api/v1/system/monitor/system")
    assert response.status_code == 200
    data = response.json()
    # 这个端点返回的是直接的模型数据，不是标准响应格式
    assert "cpu" in data
    assert "memory" in data
    assert "disk" in data
    assert "platform" in data
    assert "uptime_seconds" in data


@pytest.mark.asyncio
async def test_get_database_info(client: AsyncClient):
    """测试获取数据库连接池信息"""
    response = await client.get("/api/v1/system/monitor/database")
    assert response.status_code == 200
    data = response.json()
    # 这个端点返回的是直接的模型数据
    assert "pool" in data
    assert "database" in data
    assert "status" in data


@pytest.mark.asyncio
async def test_get_health_status(client: AsyncClient):
    """测试获取整体健康状态"""
    response = await client.get("/api/v1/system/monitor/health")
    assert response.status_code == 200
    data = response.json()
    # 这个端点返回的是直接的模型数据
    assert "overall" in data
    assert "checks" in data
    assert "timestamp" in data
    # 验证健康状态值
    assert data["overall"] in ["healthy", "degraded", "unhealthy"]


@pytest.mark.asyncio
async def test_get_process_info(client: AsyncClient):
    """测试获取当前进程信息"""
    response = await client.get("/api/v1/system/monitor/process")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    process = data["data"]
    assert "pid" in process
    assert "memory_mb" in process
    assert "cpu_percent" in process
    assert "num_threads" in process
