"""
在线用户监控 API 测试
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_online_users(client: AsyncClient):
    """测试获取在线用户列表"""
    response = await client.get("/api/v1/system/online-users")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_online_user_stats(client: AsyncClient):
    """测试获取在线用户统计"""
    response = await client.get("/api/v1/system/online-users/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    stats = data["data"]
    assert "online_count" in stats
    assert "active_count" in stats
    assert "today_login" in stats
    assert "peak_count" in stats


@pytest.mark.asyncio
async def test_user_heartbeat(client: AsyncClient):
    """测试用户心跳接口"""
    response = await client.post("/api/v1/system/online-users/heartbeat")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    assert "user_id" in data["data"]
    assert "timestamp" in data["data"]


@pytest.mark.asyncio
async def test_get_user_sessions(client: AsyncClient):
    """测试获取用户会话列表"""
    # 使用一个示例用户ID
    user_id = "00000000-0000-0000-0000-000000000001"
    response = await client.get(f"/api/v1/system/online-users/{user_id}/sessions")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    sessions = data["data"]
    assert "user_id" in sessions
    assert "sessions" in sessions
    assert "total" in sessions
