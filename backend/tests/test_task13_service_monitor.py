"""
T13 测试：服务监控面板
测试系统资源监控、数据库连接池监控、健康状态检查 API
"""

import pytest
import pytest_asyncio
import psutil
import sys
import os
from datetime import datetime
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app


@pytest_asyncio.fixture
async def client():
    """创建测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestSystemMonitor:
    """测试系统监控 API"""

    @pytest.mark.asyncio
    async def test_get_system_info_returns_valid_data(self, client):
        """测试系统信息 API 返回有效数据"""
        response = await client.get("/api/v1/system/monitor/system")
        assert response.status_code == 200
        
        data = response.json()
        
        # 验证 CPU 信息
        assert "cpu" in data
        assert "percent" in data["cpu"]
        assert "count" in data["cpu"]
        assert 0 <= data["cpu"]["percent"] <= 100
        assert data["cpu"]["count"] > 0
        
        # 验证内存信息
        assert "memory" in data
        assert "total_gb" in data["memory"]
        assert "used_gb" in data["memory"]
        assert "percent" in data["memory"]
        assert data["memory"]["total_gb"] > 0
        assert data["memory"]["used_gb"] >= 0
        assert 0 <= data["memory"]["percent"] <= 100
        
        # 验证磁盘信息
        assert "disk" in data
        assert "total_gb" in data["disk"]
        assert "used_gb" in data["disk"]
        assert "percent" in data["disk"]
        assert data["disk"]["total_gb"] > 0
        assert 0 <= data["disk"]["percent"] <= 100
        
        # 验证平台信息
        assert "platform" in data
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_get_system_info_cpu_percent_valid_range(self, client):
        """测试 CPU 使用率在有效范围内"""
        response = await client.get("/api/v1/system/monitor/system")
        assert response.status_code == 200
        
        data = response.json()
        cpu_percent = data["cpu"]["percent"]
        
        assert isinstance(cpu_percent, (int, float))
        assert 0 <= cpu_percent <= 100

    @pytest.mark.asyncio
    async def test_get_system_info_memory_calculation(self, client):
        """测试内存计算正确性"""
        response = await client.get("/api/v1/system/monitor/system")
        assert response.status_code == 200
        
        data = response.json()
        memory = data["memory"]
        
        # used + available 应该接近 total（允许小误差）
        calculated_total = memory["used_gb"] + memory["available_gb"]
        assert abs(calculated_total - memory["total_gb"]) < 0.5

    @pytest.mark.asyncio
    async def test_get_database_info_returns_pool_status(self, client):
        """测试数据库连接池状态 API"""
        response = await client.get("/api/v1/system/monitor/database")
        assert response.status_code == 200
        
        data = response.json()
        
        # 验证连接池信息
        assert "pool" in data
        assert "pool_size" in data["pool"]
        assert "checked_out" in data["pool"]
        assert "overflow" in data["pool"]
        assert "status" in data["pool"]
        
        # 验证状态值
        assert data["pool"]["status"] in ["healthy", "degraded", "unhealthy", "unknown"]
        assert data["pool"]["pool_size"] >= 0
        assert data["pool"]["checked_out"] >= 0
        
        # 验证数据库名称
        assert "database" in data

    @pytest.mark.asyncio
    async def test_get_database_info_status_values(self, client):
        """测试数据库状态值类型"""
        response = await client.get("/api/v1/system/monitor/database")
        assert response.status_code == 200
        
        data = response.json()
        
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy", "unknown"]

    @pytest.mark.asyncio
    async def test_get_health_status_returns_overall_health(self, client):
        """测试健康状态检查 API 返回整体健康状态"""
        response = await client.get("/api/v1/system/monitor/health")
        assert response.status_code == 200
        
        data = response.json()
        
        # 验证整体状态
        assert "overall" in data
        assert data["overall"] in ["healthy", "degraded", "unhealthy"]
        
        # 验证检查详情
        assert "checks" in data
        assert "cpu" in data["checks"]
        assert "memory" in data["checks"]
        assert "disk" in data["checks"]
        assert "database" in data["checks"]
        
        # 验证时间戳
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_get_health_status_checks_structure(self, client):
        """测试健康检查详情结构"""
        response = await client.get("/api/v1/system/monitor/health")
        assert response.status_code == 200
        
        data = response.json()
        checks = data["checks"]
        
        # 每个检查项都应该有 status 和 value
        for check_name in ["cpu", "memory", "disk", "database"]:
            assert check_name in checks
            assert "status" in checks[check_name]
            assert "value" in checks[check_name] or "pool_size" in checks[check_name]

    @pytest.mark.asyncio
    async def test_get_process_info(self, client):
        """测试进程信息 API"""
        response = await client.get("/api/v1/system/monitor/process")
        assert response.status_code == 200
        
        data = response.json()
        
        # 验证进程基本信息
        assert "pid" in data
        assert "memory_mb" in data
        assert "cpu_percent" in data
        assert "num_threads" in data
        assert "status" in data
        
        # 验证数据类型
        assert isinstance(data["pid"], int)
        assert data["pid"] > 0
        assert isinstance(data["memory_mb"], (int, float))
        assert data["memory_mb"] > 0
        assert isinstance(data["num_threads"], int)
        assert data["num_threads"] > 0

    @pytest.mark.asyncio
    async def test_monitor_endpoints_all_accessible(self, client):
        """测试所有监控端点可访问"""
        endpoints = [
            "/api/v1/system/monitor/system",
            "/api/v1/system/monitor/database",
            "/api/v1/system/monitor/health",
            "/api/v1/system/monitor/process",
        ]
        
        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code == 200, f"Endpoint {endpoint} not accessible"


class TestMonitorSchema:
    """测试监控数据结构"""

    def test_system_info_schema_fields(self):
        """测试系统信息 Schema 字段"""
        from app.api.v1.system.monitor import SystemInfo, CPUInfo, MemoryInfo, DiskInfo
        
        # CPU 信息
        cpu = CPUInfo(percent=50.0, count=8)
        assert cpu.percent == 50.0
        assert cpu.count == 8
        
        # 内存信息
        memory = MemoryInfo(
            total_gb=16.0,
            used_gb=8.0,
            available_gb=8.0,
            percent=50.0
        )
        assert memory.total_gb == 16.0
        assert memory.percent == 50.0
        
        # 磁盘信息
        disk = DiskInfo(
            total_gb=500.0,
            used_gb=100.0,
            free_gb=400.0,
            percent=20.0
        )
        assert disk.total_gb == 500.0
        assert disk.percent == 20.0

    def test_database_pool_info_schema(self):
        """测试数据库连接池 Schema"""
        from app.api.v1.system.monitor import DatabasePoolInfo
        
        pool = DatabasePoolInfo(
            pool_size=10,
            checked_out=3,
            overflow=0,
            checked_in=7,
            status="healthy"
        )
        
        assert pool.pool_size == 10
        assert pool.checked_out == 3
        assert pool.status == "healthy"

    def test_health_status_schema(self):
        """测试健康状态 Schema"""
        from app.api.v1.system.monitor import HealthStatus
        
        health = HealthStatus(
            overall="healthy",
            checks={
                "cpu": {"status": "ok", "value": "45%"},
                "memory": {"status": "ok", "value": "60%"}
            },
            timestamp=datetime.now().isoformat()
        )
        
        assert health.overall == "healthy"
        assert "cpu" in health.checks
        assert "memory" in health.checks


class TestMonitorEdgeCases:
    """测试监控边界情况"""

    @pytest.mark.asyncio
    async def test_system_info_high_load_values(self, client):
        """测试高负载值"""
        response = await client.get("/api/v1/system/monitor/system")
        assert response.status_code == 200
        
        data = response.json()
        
        # 所有百分比值应该在 0-100 范围内
        assert 0 <= data["cpu"]["percent"] <= 100
        assert 0 <= data["memory"]["percent"] <= 100
        assert 0 <= data["disk"]["percent"] <= 100

    @pytest.mark.asyncio
    async def test_timestamp_format(self, client):
        """测试时间戳格式"""
        response = await client.get("/api/v1/system/monitor/system")
        assert response.status_code == 200
        
        data = response.json()
        
        # 验证时间戳可以被解析
        timestamp = data["timestamp"]
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed.year >= 2024


class TestMonitorIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_health_reflects_system_state(self, client):
        """测试健康状态反映真实系统状态"""
        # 获取系统信息
        system_response = await client.get("/api/v1/system/monitor/system")
        system_data = system_response.json()
        
        # 获取健康状态
        health_response = await client.get("/api/v1/system/monitor/health")
        health_data = health_response.json()
        
        # 验证健康检查与系统数据一致性
        cpu_check = health_data["checks"]["cpu"]
        if system_data["cpu"]["percent"] >= 90:
            assert cpu_check["status"] == "warning"
        
        memory_check = health_data["checks"]["memory"]
        if system_data["memory"]["percent"] >= 90:
            assert memory_check["status"] == "warning"

    @pytest.mark.asyncio
    async def test_database_status_consistent(self, client):
        """测试数据库状态一致性"""
        # 获取数据库状态
        db_response = await client.get("/api/v1/system/monitor/database")
        db_data = db_response.json()
        
        # 获取健康状态中的数据库检查
        health_response = await client.get("/api/v1/system/monitor/health")
        health_data = health_response.json()
        
        # 验证状态一致性
        assert health_data["checks"]["database"]["status"] == db_data["pool"]["status"]


# ==================== 测试运行 ====================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
