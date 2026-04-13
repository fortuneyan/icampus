"""
定时任务管理 API 测试
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_scheduler_tasks(client: AsyncClient):
    """测试获取定时任务列表"""
    response = await client.get("/api/v1/system/scheduler/tasks")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_scheduler_task_types(client: AsyncClient):
    """测试获取任务类型列表"""
    response = await client.get("/api/v1/system/scheduler/types")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    types = data["data"]
    assert isinstance(types, list)
    if len(types) > 0:
        assert "value" in types[0]
        assert "label" in types[0]


@pytest.mark.asyncio
async def test_create_scheduler_task(client: AsyncClient):
    """测试创建定时任务"""
    task_data = {
        "name": "测试任务",
        "task_type": "backup",
        "cron": "0 0 1 * * *",
        "description": "这是一个测试任务"
    }
    response = await client.post("/api/v1/system/scheduler/tasks", json=task_data)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    task = data["data"]
    assert task["name"] == task_data["name"]
    assert task["task_type"] == task_data["task_type"]
    assert task["cron"] == task_data["cron"]


@pytest.mark.asyncio
async def test_get_scheduler_logs(client: AsyncClient):
    """测试获取任务执行日志"""
    response = await client.get("/api/v1/system/scheduler/logs")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_scheduler_task_crud(client: AsyncClient):
    """测试定时任务的增删改查"""
    # 创建任务
    create_data = {
        "name": "CRUD测试任务",
        "task_type": "cache",
        "cron": "0 */10 * * * *",
        "description": "用于测试CRUD操作"
    }
    create_response = await client.post("/api/v1/system/scheduler/tasks", json=create_data)
    assert create_response.status_code == 200
    create_data_response = create_response.json()
    assert create_data_response["code"] == 200
    task_id = create_data_response["data"]["id"]
    
    # 获取任务详情
    get_response = await client.get(f"/api/v1/system/scheduler/tasks/{task_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["code"] == 200
    
    # 更新任务
    update_data = {"name": "更新后的任务名"}
    update_response = await client.put(f"/api/v1/system/scheduler/tasks/{task_id}", json=update_data)
    assert update_response.status_code == 200
    update_data_response = update_response.json()
    assert update_data_response["code"] == 200
    assert update_data_response["data"]["name"] == update_data["name"]
    
    # 切换任务状态
    toggle_response = await client.post(f"/api/v1/system/scheduler/tasks/{task_id}/toggle")
    assert toggle_response.status_code == 200
    toggle_data = toggle_response.json()
    assert toggle_data["code"] == 200
    
    # 删除任务
    delete_response = await client.delete(f"/api/v1/system/scheduler/tasks/{task_id}")
    assert delete_response.status_code == 200
    delete_data = delete_response.json()
    assert delete_data["code"] == 200
