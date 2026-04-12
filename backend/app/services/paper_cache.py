"""
组卷结果缓存优化服务

提供以下功能：
- 组卷结果缓存（LRU + TTL）
- 组卷快照保存与恢复
- 缓存统计与监控
- 缓存键生成（内容哈希）
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import asyncio
import json
import hashlib
import time
from collections import OrderedDict
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# ============================================================================
# 工具函数
# ============================================================================

def estimate_size(obj: Any) -> int:
    """估算对象大小（字节）"""
    try:
        return len(json.dumps(obj).encode('utf-8'))
    except Exception:
        return 0


def generate_cache_key(request: Dict[str, Any], prefix: str = "paper:") -> str:
    """
    生成缓存键
    
    使用请求内容的哈希值作为键，确保：
    - 相同内容生成相同键
    - 不同内容生成不同键
    - 顺序无关
    
    Args:
        request: 组卷请求参数
        
    Returns:
        str: 缓存键
    """
    # 按key排序确保顺序无关
    def normalize(obj):
        if isinstance(obj, dict):
            return sorted((k, normalize(v)) for k, v in obj.items())
        elif isinstance(obj, list):
            return sorted(normalize(item) for item in obj)
        else:
            return obj
    
    normalized = normalize(request)
    content = json.dumps(normalized, sort_keys=True, ensure_ascii=False)
    
    # 计算MD5哈希
    hash_value = hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
    
    return f"{prefix}{hash_value}"


# ============================================================================
# 配置类
# ============================================================================

@dataclass
class PaperCacheConfig:
    """缓存配置"""
    enabled: bool = True                    # 是否启用缓存
    ttl_seconds: int = 3600                 # 缓存TTL（秒）
    max_size_mb: int = 100                  # 最大缓存大小（MB）
    key_prefix: str = "paper:"              # 缓存键前缀
    enable_snapshot: bool = True            # 是否启用快照
    snapshot_ttl_seconds: int = 86400       # 快照TTL（秒）
    max_entries: int = 1000                 # 最大缓存条目数
    
    def __post_init__(self):
        """验证配置"""
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if self.max_size_mb <= 0:
            raise ValueError("max_size_mb must be positive")
        if not self.key_prefix:
            raise ValueError("key_prefix cannot be empty")


# ============================================================================
# LRU缓存实现
# ============================================================================

class LRUCache:
    """简单的LRU缓存实现"""
    
    def __init__(self, max_size: int = 100, ttl: Optional[float] = None):
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._max_size = max_size
        self._ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """获取值"""
        if key not in self._cache:
            return None
        
        # 检查TTL
        if self._ttl:
            if time.time() - self._timestamps[key] > self._ttl:
                self.delete(key)
                return None
        
        # 移动到末尾（最近使用）
        self._cache.move_to_end(key)
        return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """设置值"""
        # 如果已存在，更新并移动到末尾
        if key in self._cache:
            self._cache[key] = value
            self._timestamps[key] = time.time()
            self._cache.move_to_end(key)
            return
        
        # 如果超过大小限制，删除最旧的
        while len(self._cache) >= self._max_size:
            oldest_key = next(iter(self._cache))
            self.delete(oldest_key)
        
        # 添加新条目
        self._cache[key] = value
        self._timestamps[key] = time.time()
        self._cache.move_to_end(key)
    
    def delete(self, key: str) -> bool:
        """删除键"""
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]
            return True
        return False
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._timestamps.clear()
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if key not in self._cache:
            return False
        
        # 检查TTL
        if self._ttl:
            if time.time() - self._timestamps[key] > self._ttl:
                self.delete(key)
                return False
        
        return True
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)
    
    def keys(self) -> List[str]:
        """获取所有键"""
        return list(self._cache.keys())


# ============================================================================
# 缓存服务
# ============================================================================

class PaperCacheService:
    """组卷结果缓存服务"""
    
    def __init__(self, config: Optional[PaperCacheConfig] = None):
        self.config = config or PaperCacheConfig()
        self._cache = LRUCache(
            max_size=self.config.max_entries,
            ttl=self.config.ttl_seconds if self.config.enabled else None
        )
        self._hit_count = 0
        self._miss_count = 0
        self._total_memory = 0
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存的组卷结果
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Dict]: 缓存的试卷数据，不存在则返回None
        """
        cached = self._cache.get(key)
        
        if cached:
            self._hit_count += 1
            return cached
        
        self._miss_count += 1
        return None
    
    async def set(
        self, 
        key: str, 
        value: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> None:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 试卷数据
            ttl: 可选的TTL覆盖
        """
        if not self.config.enabled:
            return
        
        # 更新内存统计
        self._total_memory += estimate_size(value)
        
        # 设置缓存
        self._cache.set(key, value)
    
    async def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否成功删除
        """
        return self._cache.delete(key)
    
    async def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        self._hit_count = 0
        self._miss_count = 0
        self._total_memory = 0
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return self._cache.exists(key)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict: 统计信息
        """
        total_requests = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": round(hit_rate, 2),
            "key_count": self._cache.size(),
            "memory_size_bytes": self._total_memory,
            "memory_size_mb": round(self._total_memory / (1024 * 1024), 2),
            "max_memory_mb": self.config.max_size_mb,
            "enabled": self.config.enabled,
            "ttl_seconds": self.config.ttl_seconds
        }
    
    async def get_keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        获取匹配的缓存键
        
        Args:
            pattern: 可选的模式过滤
            
        Returns:
            List[str]: 匹配的键列表
        """
        keys = self._cache.keys()
        
        if pattern:
            keys = [k for k in keys if pattern in k]
        
        return keys


# ============================================================================
# 快照服务
# ============================================================================

class SnapshotService:
    """组卷快照服务"""
    
    def __init__(self, config: Optional[PaperCacheConfig] = None):
        self.config = config or PaperCacheConfig()
        self._snapshots: Dict[str, Dict[str, Any]] = {}
        self._snapshot_timestamps: Dict[str, float] = {}
    
    async def save_snapshot(
        self,
        request: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        保存组卷快照
        
        Args:
            request: 组卷请求
            result: 组卷结果
            
        Returns:
            Dict: 快照元数据
        """
        if not self.config.enable_snapshot:
            return {"success": False, "message": "Snapshot disabled"}
        
        # 生成快照键
        snapshot_key = generate_cache_key(request, prefix="snapshot:")
        
        # 保存快照
        self._snapshots[snapshot_key] = {
            "request": request,
            "result": result,
            "created_at": time.time()
        }
        self._snapshot_timestamps[snapshot_key] = time.time()
        
        return {
            "success": True,
            "snapshot_key": snapshot_key,
            "paper_id": result.get("id")
        }
    
    async def get_snapshot(
        self,
        request: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        获取组卷快照
        
        Args:
            request: 组卷请求
            
        Returns:
            Optional[Dict]: 快照中的试卷数据
        """
        if not self.config.enable_snapshot:
            return None
        
        # 生成快照键
        snapshot_key = generate_cache_key(request, prefix="snapshot:")
        
        # 检查快照是否存在
        if snapshot_key not in self._snapshots:
            return None
        
        # 检查TTL
        if time.time() - self._snapshot_timestamps[snapshot_key] > self.config.snapshot_ttl_seconds:
            await self.delete_snapshot(request)
            return None
        
        snapshot = self._snapshots[snapshot_key]
        return snapshot.get("result")
    
    async def delete_snapshot(self, request: Dict[str, Any]) -> bool:
        """删除快照"""
        snapshot_key = generate_cache_key(request, prefix="snapshot:")
        
        if snapshot_key in self._snapshots:
            del self._snapshots[snapshot_key]
            del self._snapshot_timestamps[snapshot_key]
            return True
        
        return False
    
    async def list_snapshots(self) -> List[Dict[str, Any]]:
        """
        列出所有快照
        
        Returns:
            List[Dict]: 快照列表
        """
        snapshots = []
        
        for key, data in self._snapshots.items():
            # 检查TTL
            age = time.time() - self._snapshot_timestamps[key]
            if age > self.config.snapshot_ttl_seconds:
                continue
            
            snapshots.append({
                "key": key,
                "paper_id": data.get("result", {}).get("id"),
                "created_at": data.get("created_at"),
                "age_seconds": int(age)
            })
        
        return snapshots
    
    async def clear_snapshots(self) -> int:
        """清空所有快照"""
        count = len(self._snapshots)
        self._snapshots.clear()
        self._snapshot_timestamps.clear()
        return count


# ============================================================================
# 缓存管理器（单例）
# ============================================================================

class CacheManager:
    """缓存管理器（单例）"""
    
    _instance: Optional['CacheManager'] = None
    
    def __init__(self):
        self._cache_service: Optional[PaperCacheService] = None
        self._snapshot_service: Optional[SnapshotService] = None
        self._config: Optional[PaperCacheConfig] = None
    
    @classmethod
    def get_instance(cls) -> 'CacheManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def initialize(self, config: Optional[PaperCacheConfig] = None):
        """初始化缓存服务"""
        self._config = config or PaperCacheConfig()
        self._cache_service = PaperCacheService(self._config)
        self._snapshot_service = SnapshotService(self._config)
    
    @property
    def cache(self) -> PaperCacheService:
        """获取缓存服务"""
        if self._cache_service is None:
            self.initialize()
        return self._cache_service
    
    @property
    def snapshot(self) -> SnapshotService:
        """获取快照服务"""
        if self._snapshot_service is None:
            self.initialize()
        return self._snapshot_service
    
    def get_config(self) -> PaperCacheConfig:
        """获取配置"""
        if self._config is None:
            self._config = PaperCacheConfig()
        return self._config


# ============================================================================
# 便捷函数
# ============================================================================

# 全局缓存管理器实例
_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取缓存管理器"""
    global _manager
    if _manager is None:
        _manager = CacheManager.get_instance()
        _manager.initialize()
    return _manager


def get_cache_service() -> PaperCacheService:
    """获取缓存服务"""
    return get_cache_manager().cache


def get_snapshot_service() -> SnapshotService:
    """获取快照服务"""
    return get_cache_manager().snapshot


# ============================================================================
# 装饰器：缓存装饰器
# ============================================================================

def cached(
    key_func=None,
    ttl: Optional[int] = None,
    use_snapshot: bool = True
):
    """
    缓存装饰器
    
    用于缓存函数结果
    
    Args:
        key_func: 生成缓存键的函数
        ttl: TTL（秒）
        use_snapshot: 是否保存快照
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = generate_cache_key({"args": args, "kwargs": kwargs})
            
            cache = get_cache_service()
            
            # 尝试获取缓存
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # 保存缓存
            await cache.set(cache_key, result, ttl=ttl)
            
            # 保存快照
            if use_snapshot:
                snapshot = get_snapshot_service()
                request = {"args": args, "kwargs": kwargs}
                await snapshot.save_snapshot(request, result)
            
            return result
        
        return wrapper
    return decorator


# ============================================================================
# 主入口
# ============================================================================

if __name__ == "__main__":
    # 测试代码
    config = PaperCacheConfig(
        enabled=True,
        ttl_seconds=3600,
        max_entries=100
    )
    
    print("Paper Cache Service initialized successfully!")
    print(f"Config: {config}")
    
    # 测试缓存键生成
    request1 = {"subject": "math", "grade": "10", "topics": ["集合", "函数"]}
    request2 = {"grade": "10", "topics": ["函数", "集合"], "subject": "math"}
    
    key1 = generate_cache_key(request1)
    key2 = generate_cache_key(request2)
    
    print(f"Request 1 key: {key1}")
    print(f"Request 2 key: {key2}")
    print(f"Keys equal: {key1 == key2}")
